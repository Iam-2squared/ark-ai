"""Generator cleanup cannot rewrite an already hashed clock result.

The source and timestamp are caller supplied, with no trusted clock, signed
issuer, permission or external ToolBackend involved.
"""

import hashlib
import sys

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def _sample(seq):
    return clock.SyntheticClockSample(
        seq, hashlib.sha256(b"local-clock-fixture").hexdigest(), seq, seq,
    )


def _distinct_equal(value):
    alternate = ("!" + value)[1:]
    assert alternate == value and alternate is not value
    return alternate


@pytest.mark.parametrize("phase", ("next_sample", "generator_finally"))
@pytest.mark.parametrize("target", ("wall", "source_carrier", "chain_carrier"))
def test_iterator_cannot_rewrite_last_constructed_clock_witness(
    phase, target,
):
    callbacks = []

    def samples():
        yield _sample(1)
        # On resumption, the suspended caller is the clock sequence loop.
        caller = sys._getframe(1)
        result = caller.f_locals["result"]
        callbacks.append(True)
        if target == "wall":
            object.__setattr__(result, "last_wall_ms", 999)
        elif target == "source_carrier":
            object.__setattr__(
                result, "source_digest", _distinct_equal(result.source_digest),
            )
        else:
            object.__setattr__(
                result, "chain_hash", _distinct_equal(result.chain_hash),
            )
        if phase == "next_sample":
            yield _sample(2)

    with pytest.raises(
        clock.SyntheticClockRejected,
        match="constructed clock witness changed",
    ):
        clock.review_synthetic_clock_sequence(samples())
    assert callbacks == [True]


def test_unchanged_clock_sequence_remains_a_non_authoritative_digest():
    result = clock.review_synthetic_clock_sequence((
        _sample(1), _sample(2),
    ))
    assert result.event_count == 2
    assert result.last_wall_ms == 2
    assert result.last_monotonic_ns == 2
    assert result.chain_hash.startswith("clk_")
    assert result.trusted_clock_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
