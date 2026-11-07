"""Disconnected scheduler reviews pin their SQLite source for every count.

No trigger preparation in this suite grants notification or Tool permission.
"""

from pathlib import Path

import pytest

import ark.proactive_synthetic_review as proactive_module
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy():
    return SyntheticTriggerPolicy("owner", "local", "fixture", 1, "rev1", 1, 100, 3)


@pytest.mark.parametrize("alternate", [False, True])
def test_count_refuses_reentrant_source_swap(
    tmp_path: Path, monkeypatch, alternate: bool,
):
    path = tmp_path / "prepared.sqlite"
    other = tmp_path / "other.sqlite"
    ledger = SyntheticProactiveLedger(path)
    before = proactive_module._validate

    def retarget(conn):
        before(conn)
        ledger.path = other if alternate else Path(str(path))

    monkeypatch.setattr(proactive_module, "_validate", retarget)
    with pytest.raises(SyntheticTriggerRejected, match="path changed"):
        ledger.count()
    assert not other.exists()


@pytest.mark.parametrize("bad_path", [None, "not-a-Path"])
def test_count_rejects_invalid_source_before_open(tmp_path: Path, bad_path):
    path = tmp_path / "prepared.sqlite"
    ledger = SyntheticProactiveLedger(path)
    ledger.path = bad_path
    with pytest.raises(SyntheticTriggerRejected, match="path changed"):
        ledger.count()


def test_stable_count_reflects_inert_preparation(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite")
    assert ledger.count() == 0
    receipt = ledger.prepare(
        _policy(), source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=10, now_ms=10,
    )
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert ledger.count() == 1
