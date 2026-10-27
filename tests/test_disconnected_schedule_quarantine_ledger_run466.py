"""Only explicit expired synthetic occurrences may become durable quarantine rows."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    QuarantineWitness,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


def policy(**kwargs):
    data = dict(policy_sha256="a" * 64, first_ms=10_000, interval_ms=5_000,
                count=3, grace_ms=500)
    data.update(kwargs)
    return QuarantinePolicy(**data)


def fresh(tmp_path, p=None):
    p = p or policy()
    path = tmp_path / "quarantine.db"
    return (DisconnectedScheduleQuarantineLedger(path, policy=p, create=True), p, path)


def advance(db, p, i, witness, now):
    return db.quarantine_expired(index=i,
        occurrence_id=derive_quarantined_occurrence(p, i),
        observed_ms=now, retained=witness)


def test_restart_and_caller_retained_witness_only(tmp_path):
    db, p, path = fresh(tmp_path)
    first = genesis_quarantine_witness(p)
    assert db.inspect(retained=first) == first
    result = advance(db, p, 0, first, 10_501)
    assert result.witness.count == 1 and result.quarantined_index == 0
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=p)
    assert reopened.inspect(retained=result.witness) == result.witness
    for attr in ("execution_authorized", "notification_authorized",
                 "automatic_replay_authorized", "trusted_clock_verified", "consent_verified"):
        assert getattr(result, attr) is False
    assert result.witness.independently_authenticated is False


def test_no_skip_duplicate_or_stale_witness(tmp_path):
    db, p, _ = fresh(tmp_path)
    origin = genesis_quarantine_witness(p)
    with pytest.raises(ScheduleQuarantineRejected, match="out-of-order"):
        advance(db, p, 1, origin, 15_501)
    current = advance(db, p, 0, origin, 10_501).witness
    with pytest.raises(ScheduleQuarantineRejected, match="stale"):
        advance(db, p, 1, origin, 15_501)
    with pytest.raises(ScheduleQuarantineRejected, match="out-of-order"):
        advance(db, p, 0, current, 10_501)
    assert db.inspect(retained=current) == current


@pytest.mark.parametrize("now", [9_999, 10_000, 10_500])
def test_not_yet_expired_refused(tmp_path, now):
    db, p, _ = fresh(tmp_path)
    with pytest.raises(ScheduleQuarantineRejected, match="not expired"):
        advance(db, p, 0, genesis_quarantine_witness(p), now)


def test_second_step_observed_clock_cannot_regress(tmp_path):
    db, p, _ = fresh(tmp_path)
    first = advance(db, p, 0, genesis_quarantine_witness(p), 30_000).witness
    with pytest.raises(ScheduleQuarantineRejected, match="regressed"):
        advance(db, p, 1, first, 16_000)
    assert db.inspect(retained=first) == first


def test_exhausted_schedule_quarantine_without_dispatch(tmp_path):
    db, p, _ = fresh(tmp_path)
    witness = genesis_quarantine_witness(p)
    for i in range(3):
        witness = advance(db, p, i, witness, 30_000 + i).witness
    assert witness.count == 3
    with pytest.raises(ScheduleQuarantineRejected, match="outside policy"):
        db.quarantine_expired(index=3, occurrence_id="slot_" + "0" * 64,
                              observed_ms=30_003, retained=witness)


def test_mismatched_schedule_and_wrong_occurrence(tmp_path):
    db, p, path = fresh(tmp_path)
    wrong = policy(policy_sha256="b" * 64)
    with pytest.raises(ScheduleQuarantineRejected, match="stored schedule"):
        DisconnectedScheduleQuarantineLedger(path, policy=wrong)
    with pytest.raises(ScheduleQuarantineRejected, match="not policy-bound"):
        db.quarantine_expired(index=0,
            occurrence_id=derive_quarantined_occurrence(wrong, 0),
            observed_ms=12_000, retained=genesis_quarantine_witness(p))


def test_crash_before_external_retention_refuses_old_witness(tmp_path):
    db, p, path = fresh(tmp_path)
    old = genesis_quarantine_witness(p)
    advance(db, p, 0, old, 10_501)
    with pytest.raises(ScheduleQuarantineRejected, match="stale"):
        DisconnectedScheduleQuarantineLedger(path, policy=p).inspect(retained=old)


def test_sqlite_mutation_chain_and_dropped_row_fail_closed(tmp_path):
    db, p, path = fresh(tmp_path)
    current = advance(db, p, 0, genesis_quarantine_witness(p), 10_501).witness
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE quarantines SET observed_ms=observed_ms+1 WHERE seq=1")
    with pytest.raises(ScheduleQuarantineRejected, match="chain altered"):
        db.inspect(retained=current)


def test_policy_row_tamper_and_unexpected_schema_fail_closed(tmp_path):
    db, p, path = fresh(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE policy SET interval_ms=6000")
    with pytest.raises(ScheduleQuarantineRejected, match="stored schedule"):
        db.inspect(retained=genesis_quarantine_witness(p))
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE policy SET interval_ms=5000")
        conn.execute("CREATE TABLE extraneous (x)")
    with pytest.raises(ScheduleQuarantineRejected, match="schema drift"):
        db.inspect(retained=genesis_quarantine_witness(p))


def test_missing_db_never_recreated(tmp_path):
    db, p, path = fresh(tmp_path)
    path.unlink()
    with pytest.raises(ScheduleQuarantineRejected, match="missing"):
        db.inspect(retained=genesis_quarantine_witness(p))
    assert not path.exists()


def test_one_winner_at_sqlite_boundary(tmp_path):
    db, p, path = fresh(tmp_path)
    witness = genesis_quarantine_witness(p)

    def attempt(_):
        try:
            reopened = DisconnectedScheduleQuarantineLedger(path, policy=p)
            advance(reopened, p, 0, witness, 10_501)
            return True
        except ScheduleQuarantineRejected:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        winners = list(pool.map(attempt, range(16)))
    assert winners.count(True) == 1
    assert winners.count(False) == 15


@pytest.mark.parametrize("bad", [
    policy(policy_sha256="A" * 64), policy(first_ms=True), policy(first_ms=-1),
    policy(interval_ms=999), policy(interval_ms=0), policy(count=0),
    policy(count=4097), policy(grace_ms=-1), policy(grace_ms=60_001),
    policy(first_ms=2**63 - 200, count=2),
])
def test_bad_policy_rejected(tmp_path, bad):
    with pytest.raises(ScheduleQuarantineRejected):
        fresh(tmp_path, bad)


@pytest.mark.parametrize("witness", [None, True, QuarantineWitness(True, "a" * 64),
    QuarantineWitness(0, "x" * 64), QuarantineWitness(-1, "a" * 64)])
def test_bad_retained_witness_rejected(tmp_path, witness):
    db, p, _ = fresh(tmp_path)
    with pytest.raises(ScheduleQuarantineRejected):
        advance(db, p, 0, witness, 10_501)


def test_symlink_ancestor_and_hardlink_alias_refused(tmp_path):
    db, p, path = fresh(tmp_path)
    alias = tmp_path / "alias.db"
    alias.hardlink_to(path)
    with pytest.raises(ScheduleQuarantineRejected, match="aliased"):
        db.inspect(retained=genesis_quarantine_witness(p))
    alias.unlink()
    link = tmp_path / "symlink"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("OS cannot create directory symlink in this test")
    with pytest.raises(ScheduleQuarantineRejected, match="ancestor"):
        DisconnectedScheduleQuarantineLedger(link / path.name, policy=p)


def test_occurrence_matches_previous_preview_formula():
    import hashlib
    import json
    p = policy()
    for index in range(p.count):
        payload = json.dumps((p.policy_sha256, index,
            p.first_ms + index * p.interval_ms), separators=(",", ":")).encode("ascii")
        assert derive_quarantined_occurrence(p, index) == "slot_" + hashlib.sha256(
            b"ARK-disconnected-schedule-preview-v1\0" + b"occurrence\0" + payload
        ).hexdigest()
