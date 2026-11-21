"""Synthetic caller-clock witnesses retain their original identity carriers.

These timing values are untrusted fixture inputs, never clock attestation.
"""

import hashlib

import pytest

from ark.agency.synthetic_clock_sequence_review import (
    SyntheticClockRejected,
    SyntheticClockSample,
    review_synthetic_clock_sequence,
)


def _sample(seq):
    source = hashlib.sha256(b"disconnected-source").hexdigest()
    return SyntheticClockSample(seq, source, seq * 10, seq * 100)


def _clone_string(value):
    cloned = value.encode("ascii").decode("ascii")
    assert cloned == value and cloned is not value
    return cloned


def test_equal_digest_carrier_replacement_between_samples_fails():
    first = _sample(1)

    def stream():
        yield first
        object.__setattr__(
            first, "source_digest", _clone_string(first.source_digest),
        )
        yield _sample(2)

    with pytest.raises(SyntheticClockRejected, match="prior clock sample changed"):
        review_synthetic_clock_sequence(stream())


def test_equal_digest_carrier_replacement_on_generator_close_fails():
    first = _sample(1)

    def stream():
        try:
            yield first
        finally:
            object.__setattr__(
                first, "source_digest", _clone_string(first.source_digest),
            )

    with pytest.raises(SyntheticClockRejected, match="prior clock sample changed"):
        review_synthetic_clock_sequence(stream())


def test_retained_equal_chain_carrier_replacement_is_not_silent():
    first = _sample(1)
    witness = review_synthetic_clock_sequence((first,))

    def stream():
        object.__setattr__(
            witness, "chain_hash", _clone_string(witness.chain_hash),
        )
        yield first

    with pytest.raises(SyntheticClockRejected, match="witness changed"):
        review_synthetic_clock_sequence(stream(), retained=witness)


def test_retained_history_over_requested_budget_rejects_before_iteration():
    witness = review_synthetic_clock_sequence((_sample(1), _sample(2)))

    class ForbiddenIterator:
        def __iter__(self):
            raise AssertionError("impossible retained prefix must be rejected first")

    with pytest.raises(SyntheticClockRejected, match="exceeds sample budget"):
        review_synthetic_clock_sequence(
            ForbiddenIterator(), retained=witness, max_samples=1,
        )


def test_valid_retained_extension_stays_inert():
    first = _sample(1)
    witness = review_synthetic_clock_sequence((first,))
    extended = review_synthetic_clock_sequence(
        (first, _sample(2)), retained=witness, max_samples=2,
    )
    assert extended.event_count == 2
    assert not extended.trusted_clock_verified
    assert not extended.dispatch_authorized
    assert not extended.automatic_replay_authorized
