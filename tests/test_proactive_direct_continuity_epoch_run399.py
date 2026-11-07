"""Direct proactive continuity must not accept reentrant witness replacement.

This is a disconnected history comparison, not notification, consent,
clock attestation or a grant to dispatch tools.
"""

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
)


@pytest.mark.parametrize("phase", ("retained_integrity", "current_integrity"))
@pytest.mark.parametrize("changed", ("retained", "current"))
def test_direct_continuity_pins_both_witnesses_before_integrity_callbacks(
    tmp_path, monkeypatch, phase, changed,
):
    ledger = SyntheticProactiveLedger(tmp_path / "triggers.sqlite")
    policy = SyntheticTriggerPolicy(
        "test-owner", "test-namespace", "test-trigger", 1,
        "policy-v1", 1, 1000, 10,
    )
    ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=10, now_ms=20,
    )
    prior = read_proactive_witness(ledger)
    current = read_proactive_witness(ledger)
    source = prior if phase == "retained_integrity" else current
    victim = prior if changed == "retained" else current
    old_rows = victim.row_hashes
    assert old_rows
    calls = 0
    original = SyntheticTriggerWitness.assert_integrity

    def integrity_with_reflection(self):
        nonlocal calls
        original(self)
        if self is source:
            calls += 1
            new_rows = tuple(list(old_rows))
            assert new_rows == old_rows and new_rows is not old_rows
            object.__setattr__(victim, "row_hashes", new_rows)

    monkeypatch.setattr(
        SyntheticTriggerWitness, "assert_integrity", integrity_with_reflection,
    )
    with pytest.raises(SyntheticTriggerRejected, match="proactive history witness changed"):
        assert_proactive_history_continues(prior, current)
    assert calls == 1
    assert victim.row_hashes == old_rows

    monkeypatch.undo()
    object.__setattr__(victim, "row_hashes", old_rows)
    assert_proactive_history_continues(prior, current)
    assert ledger.count() == 1
