"""Retained synthetic proactive witnesses detect removed/replaced trigger rows."""

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.proactive_synthetic_continuity_review import (
    SyntheticTriggerWitness,
    assert_proactive_history_continues,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
    _hash,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def _setup(tmp_path: Path):
    path = tmp_path / "proactive #fixture%.sqlite"
    return SyntheticProactiveLedger(path), path


def _prepare(ledger, *, now=100, observation=A):
    policy = SyntheticTriggerPolicy(
        "synthetic-user", "private", "offline-observation", 1, "v1", 1, 10, 3,
    )
    return ledger.prepare(
        policy, source_digest=B, observation_digest=observation,
        observed_at_ms=now, now_ms=now,
    )


def test_empty_history_is_canonical_and_actionless(tmp_path: Path):
    ledger, _path = _setup(tmp_path)
    witness = read_proactive_witness(ledger)
    assert witness.row_hashes == ()
    assert witness.digest.startswith("synthetic_triggers_")
    witness.assert_integrity()
    assert read_proactive_witness(ledger, retained=witness) == witness


def test_fresh_rows_append_and_preserve_older_independent_witness(tmp_path: Path):
    ledger, path = _setup(tmp_path)
    first = read_proactive_witness(ledger)
    _prepare(ledger, now=100, observation=A)
    second = read_proactive_witness(ledger, retained=first)
    assert len(second.row_hashes) == 1
    _prepare(ledger, now=101, observation=C)
    third = read_proactive_witness(SyntheticProactiveLedger(path), retained=second)
    assert len(third.row_hashes) == 2
    assert third.digest != second.digest
    assert_proactive_history_continues(first, third)
    assert_proactive_history_continues(second, third)


def test_deleted_trigger_is_visible_only_against_independent_history(tmp_path: Path):
    ledger, path = _setup(tmp_path)
    _prepare(ledger)
    retained = read_proactive_witness(ledger)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_prepared_triggers")
    assert len(read_proactive_witness(ledger).row_hashes) == 0
    with pytest.raises(SyntheticTriggerRejected, match="retained proactive trigger history"):
        read_proactive_witness(ledger, retained=retained)


def test_rewritten_valid_row_with_recomputed_primary_key_is_detected(tmp_path: Path):
    ledger, path = _setup(tmp_path)
    _prepare(ledger)
    retained = read_proactive_witness(ledger)
    with sqlite3.connect(path) as conn:
        scope, policy, source, _observation = conn.execute(
            "SELECT scope_digest,policy_digest,source_digest,observation_digest "
            "FROM synthetic_prepared_triggers"
        ).fetchone()
        new_id = "trigger_" + _hash(
            "ARK-trigger-occurrence-v1", (scope, policy, source, D),
        )
        conn.execute(
            "UPDATE synthetic_prepared_triggers SET trigger_id=?,observation_digest=?",
            (new_id, D),
        )
    # A coordinated local rewrite can pass the current schema/row guard.
    assert len(read_proactive_witness(ledger).row_hashes) == 1
    with pytest.raises(SyntheticTriggerRejected, match="retained proactive trigger history"):
        read_proactive_witness(ledger, retained=retained)


def test_single_field_corruption_rejected_without_any_retained_witness(tmp_path: Path):
    ledger, path = _setup(tmp_path)
    _prepare(ledger)
    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE synthetic_prepared_triggers SET source_digest=?", (C,))
    with pytest.raises(SyntheticTriggerRejected, match="identity does not match"):
        read_proactive_witness(ledger)


def test_retained_witness_tampering_is_rejected(tmp_path: Path):
    ledger, _path = _setup(tmp_path)
    _prepare(ledger)
    retained = read_proactive_witness(ledger)
    with pytest.raises(SyntheticTriggerRejected, match="witness integrity"):
        read_proactive_witness(ledger, retained=replace(retained, digest="0" * 64))
    with pytest.raises(SyntheticTriggerRejected, match="witness integrity"):
        read_proactive_witness(ledger, retained=replace(retained, row_hashes=("bad",)))


@pytest.mark.parametrize("invalid", [None, "witness", True, 42])
def test_wrong_retained_type_fails_closed(tmp_path: Path, invalid):
    ledger, _path = _setup(tmp_path)
    if invalid is None:
        assert read_proactive_witness(ledger, retained=None).row_hashes == ()
    else:
        with pytest.raises(SyntheticTriggerRejected, match="exact retained"):
            read_proactive_witness(ledger, retained=invalid)


def test_direct_continuity_rejects_wrong_witness_type(tmp_path: Path):
    ledger, _path = _setup(tmp_path)
    good = read_proactive_witness(ledger)
    with pytest.raises(SyntheticTriggerRejected, match="exact proactive witnesses"):
        assert_proactive_history_continues(good, object())
    with pytest.raises(SyntheticTriggerRejected, match="exact proactive witnesses"):
        assert_proactive_history_continues(object(), good)


def test_noncanonical_duplicate_witness_is_rejected():
    row = "f" * 64
    bogus = SyntheticTriggerWitness((row, row), "synthetic_triggers_" + "0" * 64)
    with pytest.raises(SyntheticTriggerRejected, match="witness integrity"):
        bogus.assert_integrity()


def test_missing_database_is_not_recreated_by_review(tmp_path: Path):
    ledger, path = _setup(tmp_path)
    path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        read_proactive_witness(ledger)
    assert not path.exists()


def test_schema_version_drift_fails_without_repair(tmp_path: Path):
    ledger, path = _setup(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(SyntheticTriggerRejected, match="schema version"):
        read_proactive_witness(ledger)
