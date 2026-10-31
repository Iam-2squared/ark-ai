"""Unauthenticated clock samples must never become live action authority."""

import hashlib

import pytest

from ark.agency.synthetic_clock_sequence_review import (
    EMPTY_CLOCK_WITNESS,
    SyntheticClockRejected,
    SyntheticClockSample,
    review_synthetic_clock_sequence,
)


def _digest(name="fixture"):
    return hashlib.sha256(name.encode()).hexdigest()


def _sample(seq, wall, monotonic, *, source=None):
    return SyntheticClockSample(
        seq, _digest() if source is None else source, wall, monotonic,
    )


def test_two_samples_have_deterministic_inert_witness():
    samples = (_sample(1, 100, 1000), _sample(2, 100, 1001))
    one = review_synthetic_clock_sequence(samples)
    two = review_synthetic_clock_sequence(tuple(samples))
    assert one == two
    assert one.event_count == 2
    assert one.last_wall_ms == 100
    assert one.last_monotonic_ns == 1001
    assert one.chain_hash.startswith("clk_")
    assert one.source_digest == _digest()
    assert not one.trusted_clock_verified
    assert not one.dispatch_authorized
    assert not one.automatic_replay_authorized


@pytest.mark.parametrize(
    "bad",
    (
        _sample(1, 1, 1, source="not-digest"),
        _sample(True, 1, 1),
        _sample(2, 1, 1),
        _sample(1, -1, 1),
        _sample(1, 1, -1),
        _sample(1, 2**63, 1),
        _sample(1, 1, 2**63),
        True,
    ),
)
def test_wrong_first_sample_or_sequence_is_rejected(bad):
    with pytest.raises(SyntheticClockRejected):
        review_synthetic_clock_sequence((bad,))


@pytest.mark.parametrize(
    "second",
    (
        _sample(2, 99, 1001),
        _sample(2, 100, 1000),
        _sample(2, 101, 999),
        _sample(2, 101, 1001, source=_digest("other")),
        _sample(3, 101, 1001),
    ),
)
def test_discontinuity_refuses_untrusted_reboot_clock(second):
    with pytest.raises(
        SyntheticClockRejected, match="sequence, source or time regressed",
    ):
        review_synthetic_clock_sequence((
            _sample(1, 100, 1000), second,
        ))


def test_retained_prefix_survives_valid_extension():
    first = (_sample(1, 100, 1000),)
    witness = review_synthetic_clock_sequence(first)
    extended = review_synthetic_clock_sequence(
        first + (_sample(2, 101, 1005),),
        retained=witness,
    )
    assert extended.event_count == 2
    assert extended != witness
    assert extended.source_digest == witness.source_digest


def test_retained_prefix_refuses_deletion_and_divergence():
    samples = (_sample(1, 100, 1000), _sample(2, 101, 1005))
    witness = review_synthetic_clock_sequence(samples)
    with pytest.raises(SyntheticClockRejected, match="shorter"):
        review_synthetic_clock_sequence(samples[:1], retained=witness)
    with pytest.raises(SyntheticClockRejected, match="prefix differs"):
        review_synthetic_clock_sequence(
            (_sample(1, 100, 1000), _sample(2, 102, 1005)),
            retained=witness,
        )


def test_retained_clock_witness_modified_during_sample_generator():
    sample = _sample(1, 1, 1)
    witness = review_synthetic_clock_sequence((sample,))

    def samples():
        object.__setattr__(witness, "chain_hash", "clk_" + "1" * 64)
        yield sample

    with pytest.raises(SyntheticClockRejected, match="witness changed"):
        review_synthetic_clock_sequence(samples(), retained=witness)


def test_earlier_sample_changed_between_yields_is_rejected():
    first = _sample(1, 10, 10)
    second = _sample(2, 11, 11)

    def samples():
        yield first
        object.__setattr__(first, "wall_ms", 11)
        yield second

    with pytest.raises(SyntheticClockRejected, match="prior clock sample changed"):
        review_synthetic_clock_sequence(samples())


def test_earlier_sample_changed_during_generator_finally_is_rejected():
    first = _sample(1, 10, 10)

    def samples():
        try:
            yield first
        finally:
            object.__setattr__(first, "monotonic_ns", 11)

    with pytest.raises(SyntheticClockRejected, match="prior clock sample changed"):
        review_synthetic_clock_sequence(samples())


def test_iterable_budget_stops_infinite_stream_at_first_overflow():
    yielded = []

    def samples():
        index = 1
        while True:
            yielded.append(index)
            yield _sample(index, index, index)
            index += 1

    with pytest.raises(SyntheticClockRejected, match="budget exceeded"):
        review_synthetic_clock_sequence(samples(), max_samples=3)
    assert yielded == [1, 2, 3, 4]
    assert review_synthetic_clock_sequence(
        (_sample(1, 1, 1), _sample(2, 2, 2), _sample(3, 3, 3)),
        max_samples=3,
    ).event_count == 3


@pytest.mark.parametrize("bad", (None, True, 0, 1025, 2**64))
def test_invalid_clock_budget_fails_before_iteration(bad):
    with pytest.raises(SyntheticClockRejected, match="budget"):
        review_synthetic_clock_sequence((), max_samples=bad)


def test_empty_sequence_cannot_claim_clock_readiness():
    with pytest.raises(SyntheticClockRejected, match="empty clock evidence"):
        review_synthetic_clock_sequence(())
    assert EMPTY_CLOCK_WITNESS.event_count == 0
    assert not EMPTY_CLOCK_WITNESS.trusted_clock_verified


def test_wrong_retained_witness_type_is_rejected():
    with pytest.raises(SyntheticClockRejected, match="exact type"):
        review_synthetic_clock_sequence((_sample(1, 1, 1),), retained={})
