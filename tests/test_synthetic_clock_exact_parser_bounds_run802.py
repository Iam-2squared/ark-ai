"""Synthetic clock parser limits must be exact ints, never equality surrogates.

The disconnected clock digest is neither trusted time nor a dispatch permit.
"""

from __future__ import annotations

import pytest

from ark.agency import synthetic_clock_sequence_review as clock


@pytest.mark.parametrize("limit", ("_MAX", "_LIMIT"))
def test_equal_integer_subclass_limit_denied_before_callbacks(monkeypatch, limit):
    invoked = []

    class HostileInteger(int):
        def __eq__(self, other):
            invoked.append("eq")
            return True

        def __ne__(self, other):
            invoked.append("ne")
            return False

    def samples():
        invoked.append("iterator")
        yield clock.SyntheticClockSample(1, "a" * 64, 100, 101)

    with monkeypatch.context() as patch:
        original = getattr(clock, limit)
        patch.setattr(clock, limit, HostileInteger(original))
        with pytest.raises(
            clock.SyntheticClockRejected,
            match="synthetic clock digest implementation changed",
        ):
            clock.review_synthetic_clock_sequence(samples())
    assert invoked == []


def test_original_clock_limits_still_allow_inert_monotonic_fixture():
    observed = clock.review_synthetic_clock_sequence((
        clock.SyntheticClockSample(1, "a" * 64, 100, 101),
        clock.SyntheticClockSample(2, "a" * 64, 100, 102),
    ))
    assert observed.event_count == 2
    assert observed.trusted_clock_verified is False
    assert observed.dispatch_authorized is False
    assert observed.automatic_replay_authorized is False
