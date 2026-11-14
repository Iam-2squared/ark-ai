"""Offline synthetic clock retained prefixes never trust replaceable equality.

No host time, real timing attestation, ToolBackend or external action is used.
"""

from __future__ import annotations

import pytest

from ark.agency import synthetic_clock_sequence_review as clock

SOURCE = "a" * 64


def _samples():
    return (
        clock.SyntheticClockSample(1, SOURCE, 100, 1_000),
        clock.SyntheticClockSample(2, SOURCE, 101, 1_001),
    )


@pytest.mark.parametrize("field", ("chain_hash", "last_wall_ms"))
def test_forged_retained_prefix_cannot_be_accepted_by_equal_override(
    monkeypatch, field,
):
    samples = _samples()
    witness = clock.review_synthetic_clock_sequence(samples[:1])
    replacement = (
        "clk_" + "f" * 64 if field == "chain_hash" else 99
    )
    values = [witness.event_count, witness.source_digest, witness.last_wall_ms,
              witness.last_monotonic_ns, witness.chain_hash]
    values[4 if field == "chain_hash" else 2] = replacement
    forged = clock.SyntheticClockWitness(*values)
    monkeypatch.setattr(clock.SyntheticClockWitness, "__eq__", lambda self, other: True)
    with pytest.raises(clock.SyntheticClockRejected, match="retained clock prefix differs"):
        clock.review_synthetic_clock_sequence(samples, retained=forged)


def test_false_equality_override_cannot_reject_matching_retained_prefix(monkeypatch):
    samples = _samples()
    witness = clock.review_synthetic_clock_sequence(samples[:1])
    monkeypatch.setattr(clock.SyntheticClockWitness, "__eq__", lambda self, other: False)
    result = clock.review_synthetic_clock_sequence(samples, retained=witness)
    assert result.event_count == 2
    assert result.dispatch_authorized is False
    assert result.trusted_clock_verified is False


def test_retained_prefix_check_never_calls_custom_equality(monkeypatch):
    samples = _samples()
    witness = clock.review_synthetic_clock_sequence(samples[:1])

    def forbidden_equal(_self, _other):
        raise AssertionError("replaceable clock equality was called")

    monkeypatch.setattr(clock.SyntheticClockWitness, "__eq__", forbidden_equal)
    result = clock.review_synthetic_clock_sequence(samples, retained=witness)
    assert result.event_count == 2
    assert result.automatic_replay_authorized is False
