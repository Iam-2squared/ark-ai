"""A retained-history callback cannot rebaseline a scheduler preparation."""

from pathlib import Path

import pytest

from ark.proactive_synthetic_continuity_review import (
    SyntheticTriggerWitness,
    _digest,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _state(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "safe scheduler # %.sqlite")
    policy = SyntheticTriggerPolicy(
        "private", "fixture", "offline", 1, "revision-1", 5, 100, 3,
    )
    ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=100, now_ms=100,
    )
    return ledger, policy, read_proactive_witness(ledger)


def _prepare(ledger, policy, witness):
    return ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="c" * 64,
        observed_at_ms=120, now_ms=120, retained=witness,
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("policy_revision", "revision-2"),
        ("minimum_interval_ms", 8),
    ],
)
def test_retained_validation_cannot_replace_original_policy(
    tmp_path, monkeypatch, field, replacement,
):
    ledger, policy, witness = _state(tmp_path)
    original = SyntheticTriggerWitness.assert_integrity

    def change_policy(self):
        original(self)
        if self is witness:
            object.__setattr__(policy, field, replacement)

    monkeypatch.setattr(
        SyntheticTriggerWitness, "assert_integrity", change_policy,
    )
    with pytest.raises(
        SyntheticTriggerRejected, match="policy or ledger path changed",
    ):
        _prepare(ledger, policy, witness)
    assert ledger.count() == 1


def test_retained_validation_cannot_rebase_source_to_equal_path(
    tmp_path, monkeypatch,
):
    ledger, policy, witness = _state(tmp_path)
    initial = ledger.path
    original = SyntheticTriggerWitness.assert_integrity

    def replace_source(self):
        original(self)
        if self is witness:
            ledger.path = Path(str(initial))

    monkeypatch.setattr(
        SyntheticTriggerWitness, "assert_integrity", replace_source,
    )
    with pytest.raises(
        SyntheticTriggerRejected, match="policy or ledger path changed",
    ):
        _prepare(ledger, policy, witness)
    assert ledger.path == initial
    assert ledger.path is not initial
    assert ledger.count() == 1


def test_valid_but_weaker_retained_history_substitution_is_rejected(
    tmp_path, monkeypatch,
):
    ledger, policy, witness = _state(tmp_path)
    empty = SyntheticTriggerWitness(
        (), "synthetic_triggers_" + _digest("ARK-trigger-witness-v1", ()),
    )
    empty.assert_integrity()
    original = SyntheticTriggerWitness.assert_integrity

    def replace_witness(self):
        original(self)
        if self is witness:
            object.__setattr__(self, "row_hashes", empty.row_hashes)
            object.__setattr__(self, "digest", empty.digest)

    monkeypatch.setattr(
        SyntheticTriggerWitness, "assert_integrity", replace_witness,
    )
    with pytest.raises(SyntheticTriggerRejected, match="retained proactive witness"):
        _prepare(ledger, policy, witness)
    assert ledger.count() == 1


def test_unchanged_retained_history_allows_only_inert_marker(tmp_path):
    ledger, policy, witness = _state(tmp_path)
    receipt = _prepare(ledger, policy, witness)
    assert ledger.count() == 2
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
