"""A synthetic retained proactive history has both value and tuple custody.

Value-equal tuple replacement must not rebase a witness during preparation.
No notification, backend execution, trusted clock, or consent is implied.
"""

import pytest

import ark.proactive_synthetic_continuity_review as continuity
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


@pytest.mark.parametrize("phase", ("first_integrity", "history_comparison"))
def test_proactive_prepare_rejects_equal_tuple_witness_replacement(
    tmp_path, monkeypatch, phase,
):
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "fixture-namespace", "fixture-definition", 1,
        "fixture-policy-r1", 1, 1000, 10,
    )
    ledger = SyntheticProactiveLedger(tmp_path / "triggers.sqlite")
    ledger.prepare(
        policy,
        source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=10, now_ms=20,
    )
    retained = continuity.read_proactive_witness(ledger)
    rows_at_entry = retained.row_hashes
    assert len(rows_at_entry) == 1
    calls = 0

    if phase == "first_integrity":
        original = continuity.SyntheticTriggerWitness.assert_integrity

        def integrity_with_reflection(self):
            nonlocal calls
            original(self)
            if self is retained and calls == 0:
                calls += 1
                object.__setattr__(retained, "row_hashes", tuple(list(rows_at_entry)))

        monkeypatch.setattr(
            continuity.SyntheticTriggerWitness,
            "assert_integrity",
            integrity_with_reflection,
        )
    else:
        original = continuity.assert_proactive_history_continues

        def history_with_reflection(earlier, current):
            nonlocal calls
            original(earlier, current)
            calls += 1
            object.__setattr__(retained, "row_hashes", tuple(list(rows_at_entry)))

        monkeypatch.setattr(
            continuity, "assert_proactive_history_continues",
            history_with_reflection,
        )

    with pytest.raises(SyntheticTriggerRejected, match="retained proactive witness changed"):
        ledger.prepare(
            policy,
            source_digest="c" * 64,
            observation_digest="d" * 64,
            observed_at_ms=30, now_ms=40,
            retained=retained,
        )
    assert calls == 1
    assert retained.row_hashes == rows_at_entry
    assert retained.row_hashes is not rows_at_entry

    # The failed transaction must not persist a second occurrence.
    monkeypatch.undo()
    object.__setattr__(retained, "row_hashes", rows_at_entry)
    assert ledger.count() == 1
    receipt = ledger.prepare(
        policy,
        source_digest="c" * 64,
        observation_digest="d" * 64,
        observed_at_ms=30, now_ms=40,
        retained=retained,
    )
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert ledger.count() == 2
