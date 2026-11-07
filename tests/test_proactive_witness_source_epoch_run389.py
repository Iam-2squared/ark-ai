"""Proactive history reads pin local source and independently retained facts."""

from pathlib import Path

import pytest

import ark.proactive_synthetic_continuity_review as module
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _ledger(tmp_path: Path) -> SyntheticProactiveLedger:
    return SyntheticProactiveLedger(tmp_path / "offline-triggers.sqlite")


def _prepare(ledger: SyntheticProactiveLedger, *, observation="a" * 64) -> None:
    policy = SyntheticTriggerPolicy(
        "offline", "private", "fixture", 1, "v1", 1, 10, 3,
    )
    ledger.prepare(
        policy, source_digest="b" * 64, observation_digest=observation,
        observed_at_ms=100, now_ms=100,
    )


def test_stable_trigger_history_remains_inert(tmp_path: Path):
    ledger = _ledger(tmp_path)
    retained = module.read_proactive_witness(ledger)
    _prepare(ledger)
    review = module.read_proactive_witness(ledger, retained=retained)
    assert len(review.row_hashes) == 1
    assert review != retained
    assert module.read_proactive_witness(ledger, retained=review) == review


def test_same_string_source_replacement_during_schema_validation_fails(
    tmp_path: Path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    original = module._validate

    def inject(connection):
        original(connection)
        ledger.path = Path(str(ledger.path))

    monkeypatch.setattr(module, "_validate", inject)
    with pytest.raises(SyntheticTriggerRejected, match="source|history changed"):
        module.read_proactive_witness(ledger)


def test_retained_witness_changes_to_new_valid_history_during_row_hashing(
    tmp_path: Path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    retained = module.read_proactive_witness(ledger)
    _prepare(ledger)
    newer = module.read_proactive_witness(ledger)
    original = module._digest

    def inject(label, data):
        digest = original(label, data)
        if label == "ARK-trigger-row-v1":
            object.__setattr__(retained, "row_hashes", newer.row_hashes)
            object.__setattr__(retained, "digest", newer.digest)
        return digest

    monkeypatch.setattr(module, "_digest", inject)
    with pytest.raises(SyntheticTriggerRejected, match="retained history"):
        module.read_proactive_witness(ledger, retained=retained)


def test_retained_witness_changes_after_continuity_check(
    tmp_path: Path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    retained = module.read_proactive_witness(ledger)
    _prepare(ledger)
    newer = module.read_proactive_witness(ledger)
    original = module.assert_proactive_history_continues

    def inject(earlier, current):
        original(earlier, current)
        object.__setattr__(earlier, "row_hashes", newer.row_hashes)
        object.__setattr__(earlier, "digest", newer.digest)

    monkeypatch.setattr(module, "assert_proactive_history_continues", inject)
    with pytest.raises(SyntheticTriggerRejected, match="retained history"):
        module.read_proactive_witness(ledger, retained=retained)


def test_source_change_after_continuity_check_is_rejected(tmp_path: Path, monkeypatch):
    ledger = _ledger(tmp_path)
    _prepare(ledger)
    retained = module.read_proactive_witness(ledger)
    original = module.assert_proactive_history_continues

    def inject(earlier, current):
        original(earlier, current)
        ledger.path = Path(str(ledger.path))

    monkeypatch.setattr(module, "assert_proactive_history_continues", inject)
    with pytest.raises(SyntheticTriggerRejected, match="source"):
        module.read_proactive_witness(ledger, retained=retained)
