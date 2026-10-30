"""SQLite quarantine reads and writes pin exact source/retained carriers.

Synthetic overdue slots cannot grant trusted-clock, consent, notification or
Tool execution. Reentrant failures roll back an uncommitted quarantine row.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.disconnected_schedule_quarantine_ledger as module
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


def _fixture(tmp_path):
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    return ledger, policy, path, genesis_quarantine_witness(policy)


def _quarantine(ledger, policy, retained):
    return ledger.quarantine_expired(
        index=0,
        occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=retained,
    )


def _equal_new_string(text: str) -> str:
    changed = (" " + text)[1:]
    assert changed == text and changed is not text
    return changed


def test_inspect_rejects_equal_path_object_replacement_during_open(
    tmp_path, monkeypatch,
):
    ledger, _, _, retained = _fixture(tmp_path)
    original = ledger._open

    def changed_open(*, read_only):
        conn = original(read_only=read_only)
        ledger._path = Path(str(ledger._path))
        return conn

    monkeypatch.setattr(ledger, "_open", changed_open)
    with pytest.raises(ScheduleQuarantineRejected, match="inspect carrier"):
        ledger.inspect(retained=retained)


def test_inspect_rejects_equal_witness_hash_replacement_during_validation(
    tmp_path, monkeypatch,
):
    ledger, _, path, retained = _fixture(tmp_path)
    original = module._validate

    def changed_validate(conn, epoch):
        result = original(conn, epoch)
        object.__setattr__(
            retained, "chain_sha256", _equal_new_string(retained.chain_sha256),
        )
        return result

    monkeypatch.setattr(module, "_validate", changed_validate)
    with pytest.raises(ScheduleQuarantineRejected, match="inspect carrier"):
        ledger.inspect(retained=retained)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (0,)


def test_inspect_rejects_equal_policy_tuple_replacement(tmp_path, monkeypatch):
    ledger, _, _, retained = _fixture(tmp_path)
    original = module._validate

    def changed_validate(conn, epoch):
        result = original(conn, epoch)
        ledger._epoch = tuple(list(ledger._epoch))
        return result

    monkeypatch.setattr(module, "_validate", changed_validate)
    with pytest.raises(ScheduleQuarantineRejected, match="inspect carrier"):
        ledger.inspect(retained=retained)


@pytest.mark.parametrize("mutation", ("path", "retained", "policy"))
def test_quarantine_precommit_carrier_drift_rolls_back(
    tmp_path, monkeypatch, mutation,
):
    ledger, policy, path, retained = _fixture(tmp_path)
    original = module._validate

    def changed_validate(conn, epoch):
        result = original(conn, epoch)
        if mutation == "path":
            ledger._path = Path(str(ledger._path))
        elif mutation == "retained":
            object.__setattr__(
                retained, "chain_sha256", _equal_new_string(retained.chain_sha256),
            )
        else:
            ledger._epoch = tuple(list(ledger._epoch))
        return result

    monkeypatch.setattr(module, "_validate", changed_validate)
    with pytest.raises(ScheduleQuarantineRejected, match="write carrier"):
        _quarantine(ledger, policy, retained)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (0,)


def test_unchanged_fixture_restart_and_no_execution_authority(tmp_path):
    ledger, policy, path, retained = _fixture(tmp_path)
    assert ledger.inspect(retained=retained) == retained
    receipt = _quarantine(ledger, policy, retained)
    assert receipt.quarantined_index == 0
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.trusted_clock_verified is False
    reopened = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert reopened.inspect(retained=receipt.witness) == receipt.witness
