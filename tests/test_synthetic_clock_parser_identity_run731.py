"""Caller clocks must not enter a substituted parser or widened budget.

Synthetic clock sequences remain unauthenticated and never grant execution.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import synthetic_clock_sequence_review as clock


@pytest.mark.parametrize("surface", (
    "digest_pattern", "chain_pattern", "max_ms", "sample_limit",
    "genesis_fields", "denial_names",
))
def test_changed_clock_parser_authority_denied_before_iterator(
    monkeypatch, surface,
):
    accessed = []

    def samples():
        accessed.append("iterator")
        raise AssertionError("substituted clock parser observed sample")
        yield clock.SyntheticClockSample(1, "a" * 64, 100, 200)

    with monkeypatch.context() as patch:
        if surface == "digest_pattern":
            patch.setattr(clock, "_DIGEST", re.compile(".*"))
        elif surface == "chain_pattern":
            patch.setattr(clock, "_CHAIN", re.compile(".*"))
        elif surface == "max_ms":
            patch.setattr(clock, "_MAX", clock._MAX - 1)
        elif surface == "sample_limit":
            patch.setattr(clock, "_LIMIT", clock._LIMIT + 1)
        elif surface == "genesis_fields":
            patch.setattr(
                clock, "_EMPTY_FIELDS", tuple(list(clock._EMPTY_FIELDS)),
            )
        else:
            patch.setattr(
                clock, "_DENIAL_NAMES", tuple(list(clock._DENIAL_NAMES)),
            )
        with pytest.raises(
            clock.SyntheticClockRejected,
            match="synthetic clock digest implementation changed",
        ):
            clock.review_synthetic_clock_sequence(samples())
    assert accessed == []


def test_original_local_clock_is_never_trusted_or_actionable():
    review = clock.review_synthetic_clock_sequence((
        clock.SyntheticClockSample(1, "a" * 64, 100, 200),
    ))
    assert review.event_count == 1
    assert review.trusted_clock_verified is False
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
