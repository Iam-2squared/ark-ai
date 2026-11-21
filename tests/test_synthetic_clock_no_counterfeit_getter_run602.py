"""Synthetic clock witnesses must not execute counterfeit class descriptors.

All samples are caller-controlled offline fixtures. A hash chain cannot prove
trusted clock provenance, human consent or authorization to dispatch tools.
"""

import pytest

from ark.agency import synthetic_clock_sequence_review as clock

_SOURCE = "a" * 64


class ClassDisguisedGetter:
    def __init__(self, original, calls):
        self.original = original
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("executed")
        return self.original if instance is None else False


def _sample(seq):
    return clock.SyntheticClockSample(seq, _SOURCE, 1000 + seq, 2000 + seq)


@pytest.mark.parametrize("flag", clock._DENIAL_NAMES)
def test_preinstalled_counterfeit_rejected_without_invoking_getter(
    monkeypatch, flag,
):
    calls = []
    original = vars(clock.SyntheticClockWitness)[flag]
    monkeypatch.setattr(
        clock.SyntheticClockWitness,
        flag,
        ClassDisguisedGetter(original, calls),
    )
    with pytest.raises(clock.SyntheticClockRejected, match="descriptor changed"):
        clock.review_synthetic_clock_sequence((_sample(1),))
    assert calls == []


@pytest.mark.parametrize("flag", clock._DENIAL_NAMES)
def test_late_counterfeit_rejected_without_invoking_getter(
    monkeypatch, flag,
):
    calls = []

    def sequence():
        yield _sample(1)
        original = vars(clock.SyntheticClockWitness)[flag]
        monkeypatch.setattr(
            clock.SyntheticClockWitness,
            flag,
            ClassDisguisedGetter(original, calls),
        )
        yield _sample(2)

    with pytest.raises(clock.SyntheticClockRejected, match="descriptor changed"):
        clock.review_synthetic_clock_sequence(sequence())
    assert calls == []


@pytest.mark.parametrize("flag", clock._DENIAL_NAMES)
def test_retained_witness_rejects_counterfeit_without_getter(
    monkeypatch, flag,
):
    retained = clock.review_synthetic_clock_sequence((_sample(1),))
    calls = []
    original = vars(clock.SyntheticClockWitness)[flag]
    monkeypatch.setattr(
        clock.SyntheticClockWitness,
        flag,
        ClassDisguisedGetter(original, calls),
    )
    with pytest.raises(clock.SyntheticClockRejected, match="descriptor changed"):
        clock.review_synthetic_clock_sequence(
            (_sample(1), _sample(2)), retained=retained,
        )
    assert calls == []


def test_unchanged_retained_prefix_remains_non_authorizing():
    retained = clock.review_synthetic_clock_sequence((_sample(1),))
    result = clock.review_synthetic_clock_sequence(
        (_sample(1), _sample(2)), retained=retained,
    )
    assert result.event_count == 2
    assert result.trusted_clock_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
