"""Reject locally forged occurrence-witness logic before any validator runs.

The disconnected ledger contains no real authorization or external effects.
"""

import pytest

import ark.agency.synthetic_occurrence_continuity_review as review
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)


@pytest.mark.parametrize("target", ("validator", "constructor", "class"))
def test_preinstalled_witness_implementation_is_denied_before_execution(
    tmp_path, monkeypatch, target,
):
    path = tmp_path / "synthetic.sqlite"
    SyntheticOccurrenceStore(path)
    retained = review.read_synthetic_ledger_witness(path)
    called = []

    if target == "validator":
        def forged_validator(self):
            called.append("validator")
            return None

        monkeypatch.setattr(review.SyntheticLedgerWitness, "assert_integrity",
                            forged_validator)
    elif target == "constructor":
        def forged_init(self, *args):
            called.append("constructor")

        monkeypatch.setattr(review.SyntheticLedgerWitness, "__init__", forged_init)
    else:
        class CounterfeitWitness:
            pass

        monkeypatch.setattr(review, "SyntheticLedgerWitness", CounterfeitWitness)

    with pytest.raises(SyntheticReplayRejected, match="implementation changed"):
        review.assert_synthetic_history_continues(retained, retained)
    with pytest.raises(SyntheticReplayRejected, match="implementation changed"):
        review.read_synthetic_ledger_witness(path, retained=retained)
    assert not called


def test_witness_validator_rebinding_during_hash_cannot_become_baseline(
    tmp_path, monkeypatch,
):
    path = tmp_path / "synthetic.sqlite"
    SyntheticOccurrenceStore(path)
    original_digest = review._digest
    changed = []

    def reentrant_digest(label, value):
        value_digest = original_digest(label, value)
        if label == "ARK-ledger-v1" and not changed:
            changed.append(True)
            monkeypatch.setattr(
                review.SyntheticLedgerWitness, "assert_integrity",
                lambda self: None,
            )
        return value_digest

    monkeypatch.setattr(review, "_digest", reentrant_digest)
    with pytest.raises(SyntheticReplayRejected, match="implementation changed"):
        review.read_synthetic_ledger_witness(path)
    assert changed


def test_unchanged_witness_read_still_accepts_exact_retained_snapshot(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    SyntheticOccurrenceStore(path)
    retained = review.read_synthetic_ledger_witness(path)
    latest = review.read_synthetic_ledger_witness(path, retained=retained)
    assert latest == retained
    assert review.assert_synthetic_history_continues(retained, latest) is None
