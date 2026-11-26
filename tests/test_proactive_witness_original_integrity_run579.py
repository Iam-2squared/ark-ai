"""Original trigger-witness integrity remains mandatory after patched callbacks.

Only local disconnected SQLite fixtures are used; no notifications, trusted
clock, consent, real scheduler execution or external authority is obtained.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.proactive_synthetic_continuity_review import (
    SyntheticTriggerWitness,
    assert_proactive_history_continues,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerRejected,
)


def _bad(witness: SyntheticTriggerWitness) -> SyntheticTriggerWitness:
    invalid = replace(
        witness, digest="synthetic_triggers_" + "f" * 64,
    )
    assert invalid.digest != witness.digest
    return invalid


@pytest.mark.parametrize("target", ("retained", "current"))
def test_direct_history_witness_uses_original_validator_when_method_is_noop(
    tmp_path, monkeypatch, target,
):
    ledger = SyntheticProactiveLedger(tmp_path / "direct-history.sqlite")
    good = read_proactive_witness(ledger)
    bad = _bad(good)

    def fake_validator(self):
        return None

    with monkeypatch.context() as patch:
        patch.setattr(SyntheticTriggerWitness, "assert_integrity", fake_validator)
        retained, current = (bad, good) if target == "retained" else (good, bad)
        with pytest.raises(SyntheticTriggerRejected, match="witness integrity"):
            assert_proactive_history_continues(retained, current)
    assert ledger.count() == 0


def test_retained_history_read_refuses_patched_noop_validator(tmp_path, monkeypatch):
    ledger = SyntheticProactiveLedger(tmp_path / "retained-history.sqlite")
    good = read_proactive_witness(ledger)
    bad = _bad(good)

    with monkeypatch.context() as patch:
        patch.setattr(SyntheticTriggerWitness, "assert_integrity", lambda _self: None)
        with pytest.raises(SyntheticTriggerRejected, match="witness integrity"):
            read_proactive_witness(ledger, retained=bad)
    assert ledger.count() == 0


def test_normal_trigger_witness_remains_local_and_inert(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "normal-history.sqlite")
    witness = read_proactive_witness(ledger)
    observed = read_proactive_witness(ledger, retained=witness)
    assert observed == witness
    assert_proactive_history_continues(witness, observed)
    assert ledger.count() == 0
