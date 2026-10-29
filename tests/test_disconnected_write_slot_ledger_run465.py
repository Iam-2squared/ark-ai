"""Detached durable WRITE reservation invariants; no real effect or approval."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerRejected,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)


def claim(i, *, plan=1, request=None):
    p = "plan_" + f"{plan:064x}"
    s = "step_" + f"{i:016x}"
    r = request or f"{i:064x}"
    return DetachedWriteSlotClaim(derive_disconnected_write_slot_id(p, s, r), p, s, r)


def ledger(tmp_path):
    return DisconnectedWriteSlotLedger(tmp_path / "synthetic.db", create=True)


def attempt(path, witness, item):
    try:
        DisconnectedWriteSlotLedger(Path(path)).reserve_many((item,), retained=witness)
    except WriteSlotLedgerRejected:
        return False
    return True


def test_genesis_and_atomic_append_reopen_no_write_authority(tmp_path):
    item = ledger(tmp_path)
    prior = genesis_write_slot_witness()
    assert item.inspect(retained=prior) == prior
    result = item.reserve_many((claim(1), claim(2)), retained=prior)
    assert result.added_count == 2 and result.witness.count == 2
    assert result.witness.chain_sha256 != prior.chain_sha256
    for name in ("dispatch_authorized", "automatic_replay_authorized",
                 "exact_once_external_effect_proven", "trusted_clock_verified",
                 "owner_or_consent_verified"):
        assert getattr(result, name) is False
    assert not result.witness.independently_authenticated
    assert DisconnectedWriteSlotLedger(tmp_path / "synthetic.db").inspect(
        retained=result.witness,
    ) == result.witness
    assert "plan_" not in repr(claim(1)) and "step_" not in repr(claim(1))
    assert "slot_" not in repr(claim(1))
    with pytest.raises(FrozenInstanceError):
        result.added_count = 3


def test_repeat_reservation_on_reopen_never_allowed(tmp_path):
    db = ledger(tmp_path)
    first = db.reserve_many((claim(1),), retained=genesis_write_slot_witness()).witness
    with pytest.raises(WriteSlotLedgerRejected, match="duplicate"):
        DisconnectedWriteSlotLedger(tmp_path / "synthetic.db").reserve_many(
            (claim(1),), retained=first,
        )
    assert db.inspect(retained=first) == first


def test_same_plan_step_with_changed_request_is_forbidden(tmp_path):
    db = ledger(tmp_path)
    witness = db.reserve_many((claim(1),), retained=genesis_write_slot_witness()).witness
    with pytest.raises(WriteSlotLedgerRejected, match="duplicate"):
        db.reserve_many((claim(1, request="f" * 64),), retained=witness)
    assert db.inspect(retained=witness) == witness


def test_identical_step_across_distinct_plans_allowed_with_distinct_ids(tmp_path):
    db = ledger(tmp_path)
    receipt = db.reserve_many((claim(1, plan=1), claim(1, plan=2)),
                              retained=genesis_write_slot_witness())
    assert receipt.witness.count == 2


def test_stale_witness_and_unretained_post_commit_window_are_fail_closed(tmp_path):
    db = ledger(tmp_path)
    old = genesis_write_slot_witness()
    current = db.reserve_many((claim(1),), retained=old).witness
    with pytest.raises(WriteSlotLedgerRejected, match="stale"):
        db.reserve_many((claim(2),), retained=old)
    with pytest.raises(WriteSlotLedgerRejected, match="stale"):
        db.inspect(retained=old)
    assert db.inspect(retained=current) == current


def test_duplicate_batch_rolls_back_every_insert(tmp_path):
    db = ledger(tmp_path)
    old = genesis_write_slot_witness()
    with pytest.raises(WriteSlotLedgerRejected, match="duplicate"):
        db.reserve_many((claim(1), claim(1)), retained=old)
    with pytest.raises(WriteSlotLedgerRejected, match="duplicate"):
        db.reserve_many((claim(1), claim(1, request="f" * 64)), retained=old)
    assert db.inspect(retained=old) == old


def test_batch_conflict_with_previous_history_rolls_back_all(tmp_path):
    db = ledger(tmp_path)
    old = db.reserve_many((claim(1),), retained=genesis_write_slot_witness()).witness
    with pytest.raises(WriteSlotLedgerRejected, match="duplicate"):
        db.reserve_many((claim(2), claim(1)), retained=old)
    assert db.inspect(retained=old) == old


def test_max_batch_boundary_and_capacity(tmp_path):
    db = ledger(tmp_path)
    current = genesis_write_slot_witness()
    for section in range(32):
        group = tuple(claim(section * 16 + i + 1) for i in range(16))
        current = db.reserve_many(group, retained=current).witness
    assert current.count == 512
    with pytest.raises(WriteSlotLedgerRejected, match="capacity"):
        db.reserve_many((claim(513),), retained=current)
    assert db.inspect(retained=current) == current


def test_invalid_batch_size_and_input_shapes(tmp_path):
    db = ledger(tmp_path)
    initial = genesis_write_slot_witness()
    for incoming in ((), [claim(1)], (claim(1),) * 17, (object(),), (None,)):
        with pytest.raises(WriteSlotLedgerRejected):
            db.reserve_many(incoming, retained=initial)
    assert db.inspect(retained=initial) == initial


@pytest.mark.parametrize("invalid", [
    replace(claim(1), slot_id="slot_" + "f" * 64),
    replace(claim(1), slot_id="SLOT_" + "0" * 64),
    replace(claim(1), plan_id="plan_" + "g" * 64),
    replace(claim(1), step_id="step_" + "f" * 17),
    replace(claim(1), request_sha256=True),
    replace(claim(1), request_sha256="F" * 64),
    replace(claim(1), request_sha256=None),
])
def test_claim_exact_types_and_binding_rejected(tmp_path, invalid):
    db = ledger(tmp_path)
    with pytest.raises(WriteSlotLedgerRejected):
        db.reserve_many((invalid,), retained=genesis_write_slot_witness())


@pytest.mark.parametrize("witness", [
    None, object(), (0, "f" * 64),
    replace(genesis_write_slot_witness(), count=True),
    replace(genesis_write_slot_witness(), count=-1),
    replace(genesis_write_slot_witness(), count=513),
    replace(genesis_write_slot_witness(), chain_sha256="F" * 64),
])
def test_witness_must_be_exact_structured_type(tmp_path, witness):
    db = ledger(tmp_path)
    with pytest.raises(WriteSlotLedgerRejected):
        db.reserve_many((claim(1),), retained=witness)


def test_thread_concurrent_same_witness_exactly_one_local_reservation(tmp_path):
    _db = ledger(tmp_path)
    witness = genesis_write_slot_witness()
    path = tmp_path / "synthetic.db"
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: attempt(path, witness, claim(1)), range(32)))
    assert sum(results) == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)


def test_process_concurrent_same_witness_exactly_one_local_reservation(tmp_path):
    ledger(tmp_path)
    path = str(tmp_path / "synthetic.db")
    witness = genesis_write_slot_witness()
    with get_context("spawn").Pool(4) as pool:
        results = pool.starmap(attempt, [(path, witness, claim(1))] * 8)
    assert sum(results) == 1


def test_missing_file_never_recreated_on_reopen(tmp_path):
    db = ledger(tmp_path)
    (tmp_path / "synthetic.db").unlink()
    with pytest.raises(WriteSlotLedgerRejected, match="missing"):
        db.inspect(retained=genesis_write_slot_witness())
    with pytest.raises(WriteSlotLedgerRejected, match="missing"):
        DisconnectedWriteSlotLedger(tmp_path / "synthetic.db")
    assert not (tmp_path / "synthetic.db").exists()


def test_existing_ledger_cannot_be_initialized_anew(tmp_path):
    ledger(tmp_path)
    with pytest.raises(WriteSlotLedgerRejected, match="existing"):
        DisconnectedWriteSlotLedger(tmp_path / "synthetic.db", create=True)


def test_parent_symlink_and_file_hardlink_rejected(tmp_path):
    actual = tmp_path / "real"
    actual.mkdir()
    DisconnectedWriteSlotLedger(actual / "fixture.db", create=True)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("filesystem disallows symlinks")
    with pytest.raises(WriteSlotLedgerRejected, match="ancestor"):
        DisconnectedWriteSlotLedger(alias / "fixture.db")
    other = actual / "hard.db"
    try:
        other.hardlink_to(actual / "fixture.db")
    except OSError:
        pytest.skip("filesystem disallows hardlinks")
    with pytest.raises(WriteSlotLedgerRejected, match="aliased"):
        DisconnectedWriteSlotLedger(actual / "fixture.db")
    other.unlink()
    assert DisconnectedWriteSlotLedger(actual / "fixture.db").inspect(
        retained=genesis_write_slot_witness(),
    ) == genesis_write_slot_witness()


def test_persisted_row_tamper_and_digest_tamper_rejected(tmp_path):
    db = ledger(tmp_path)
    witness = db.reserve_many((claim(1),), retained=genesis_write_slot_witness()).witness
    with sqlite3.connect(db._path) as conn:
        conn.execute("UPDATE synthetic_write_slots SET request_sha256=? WHERE seq=1",
                     ("f" * 64,))
    with pytest.raises(WriteSlotLedgerRejected, match="persisted"):
        db.inspect(retained=witness)


def test_schema_tamper_rejected_at_open(tmp_path):
    ledger(tmp_path)
    with sqlite3.connect(tmp_path / "synthetic.db") as conn:
        conn.execute("CREATE TABLE injected (value INTEGER)")
    with pytest.raises(WriteSlotLedgerRejected, match="schema"):
        DisconnectedWriteSlotLedger(tmp_path / "synthetic.db")


def test_tail_delete_detected_by_retained_witness(tmp_path):
    db = ledger(tmp_path)
    prior = db.reserve_many((claim(1),), retained=genesis_write_slot_witness()).witness
    witness = db.reserve_many((claim(2),), retained=prior).witness
    with sqlite3.connect(db._path) as conn:
        conn.execute("DELETE FROM synthetic_write_slots WHERE seq=2")
    with pytest.raises(WriteSlotLedgerRejected, match="stale"):
        db.inspect(retained=witness)


def test_reflective_claim_mutation_during_commit_precheck_denied(tmp_path, monkeypatch):
    from ark.agency import disconnected_write_slot_ledger as module
    db = ledger(tmp_path)
    item = claim(1)
    original = module._inspect
    invoked = False

    def interfere(conn):
        nonlocal invoked
        result = original(conn)
        if not invoked:
            invoked = True
            object.__setattr__(item, "request_sha256", "f" * 64)
        return result

    monkeypatch.setattr(module, "_inspect", interfere)
    with pytest.raises(WriteSlotLedgerRejected, match="changed"):
        db.reserve_many((item,), retained=genesis_write_slot_witness())
    assert db.inspect(retained=genesis_write_slot_witness()) == genesis_write_slot_witness()
