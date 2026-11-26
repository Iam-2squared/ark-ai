"""Synthetic proactive admission cannot strand its bounded SQLite ledger.

All events and timestamps are offline fixtures, not notification permission,
trusted clock evidence, or proof of external exactly-once effects.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.proactive_synthetic_review as proactive
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "fixture-owner", "private", "synthetic-observation", 1, "v1",
        1, 10, 50,
    )


def _prepare(ledger: SyntheticProactiveLedger, observation: str, at: int):
    return ledger.prepare(
        _policy(),
        source_digest="b" * 64,
        observation_digest=observation * 64,
        observed_at_ms=at,
        now_ms=at,
    )


def test_cap_rejected_before_insert_leaves_ledger_reopenable(
    tmp_path: Path, monkeypatch,
):
    monkeypatch.setattr(proactive, "_MAX_PREPARATIONS", 2)
    path = tmp_path / "bounded.sqlite"
    ledger = SyntheticProactiveLedger(path)
    _prepare(ledger, "a", 100)
    _prepare(ledger, "c", 110)
    with sqlite3.connect(path) as conn:
        previous_rows = tuple(conn.execute(
            "SELECT trigger_id FROM synthetic_prepared_triggers ORDER BY trigger_id"
        ))
    with pytest.raises(SyntheticTriggerRejected, match="ledger capacity"):
        _prepare(ledger, "d", 120)
    restarted = SyntheticProactiveLedger(path)
    witness = read_proactive_witness(restarted)
    assert len(witness.row_hashes) == 2
    with sqlite3.connect(path) as conn:
        assert tuple(conn.execute(
            "SELECT trigger_id FROM synthetic_prepared_triggers ORDER BY trigger_id"
        )) == previous_rows


def test_capacity_is_checked_again_after_restart(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(proactive, "_MAX_PREPARATIONS", 1)
    path = tmp_path / "restart.sqlite"
    first = SyntheticProactiveLedger(path)
    _prepare(first, "a", 100)
    second = SyntheticProactiveLedger(path)
    with pytest.raises(SyntheticTriggerRejected, match="ledger capacity"):
        _prepare(second, "c", 110)
    assert len(read_proactive_witness(second).row_hashes) == 1


def test_valid_below_cap_still_keeps_inert_receipt(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(proactive, "_MAX_PREPARATIONS", 2)
    ledger = SyntheticProactiveLedger(tmp_path / "below-cap.sqlite")
    receipt = _prepare(ledger, "a", 100)
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert len(read_proactive_witness(ledger).row_hashes) == 1
