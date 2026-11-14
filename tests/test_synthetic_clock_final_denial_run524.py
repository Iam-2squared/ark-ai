"""Synthetic clock chaining must remain read-only after authority denial.

All times and sources are caller-provided, not a trusted clock or consent.
"""

from __future__ import annotations

import pytest

from ark.agency.synthetic_clock_sequence_review import (
    SyntheticClockRejected,
    SyntheticClockSample,
    SyntheticClockWitness,
    review_synthetic_clock_sequence,
)

SOURCE = "a" * 64


def samples():
    return (
        SyntheticClockSample(1, SOURCE, 1000, 10),
        SyntheticClockSample(2, SOURCE, 1001, 20),
    )


def test_two_monotonic_samples_remain_diagnostic_only():
    first, second = samples()
    result = review_synthetic_clock_sequence((first, second))
    assert type(result) is SyntheticClockWitness
    assert result.event_count == 2
    assert result.last_wall_ms == 1001
    assert result.last_monotonic_ns == 20
    assert result.chain_hash.startswith("clk_")
    assert len(result.chain_hash) == 68
    assert result.trusted_clock_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_independently_retained_local_prefix_is_consistent_not_authority():
    first, second = samples()
    retained = review_synthetic_clock_sequence((first,))
    result = review_synthetic_clock_sequence((first, second), retained=retained)
    assert result.event_count == 2
    assert retained.event_count == 1
    assert result.dispatch_authorized is False


@pytest.mark.parametrize("field,forged", [
    ("trusted_clock_verified", True),
    ("dispatch_authorized", 1),
    ("automatic_replay_authorized", "False"),
])
def test_any_non_false_clock_authority_is_rejected(monkeypatch, field, forged):
    monkeypatch.setattr(
        SyntheticClockWitness, field, property(lambda self: forged),
    )
    with pytest.raises(SyntheticClockRejected):
        review_synthetic_clock_sequence(samples())


@pytest.mark.parametrize("field,replacement", [
    ("chain_hash", "clk_" + "f" * 64),
    ("last_monotonic_ns", 999),
    ("source_digest", "b" * 64),
])
def test_false_final_denial_getter_cannot_change_chain_carrier(
    monkeypatch, field, replacement,
):
    def forged_false(self):
        if self.event_count > 0:
            object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        SyntheticClockWitness, "automatic_replay_authorized",
        property(forged_false),
    )
    with pytest.raises(SyntheticClockRejected, match="clock"):
        review_synthetic_clock_sequence(samples())


@pytest.mark.parametrize("second", [
    SyntheticClockSample(2, SOURCE, 999, 20),
    SyntheticClockSample(2, SOURCE, 1001, 10),
    SyntheticClockSample(2, "b" * 64, 1001, 20),
])
def test_regressed_or_retargeted_second_clock_sample_rejected(second):
    with pytest.raises(SyntheticClockRejected):
        review_synthetic_clock_sequence((samples()[0], second))


def test_generator_finalizer_cannot_rewrite_previous_sample():
    first = samples()[0]

    def evidence():
        try:
            yield first
        finally:
            object.__setattr__(first, "monotonic_ns", 20)

    with pytest.raises(SyntheticClockRejected):
        review_synthetic_clock_sequence(evidence())


def test_empty_clock_sequence_is_insufficient():
    with pytest.raises(SyntheticClockRejected):
        review_synthetic_clock_sequence(())
