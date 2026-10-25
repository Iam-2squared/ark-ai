"""Numeric clock sample and witness carriers are held across callbacks.

These are caller-controlled synthetic times, not trusted time or an execution
permit. Replaying a hash chain never authenticates hardware or human consent.
"""

import pytest

import ark.agency.synthetic_clock_sequence_review as clock

_SOURCE = "a" * 64


def _samples():
    return [
        clock.SyntheticClockSample(1, _SOURCE, 1000, 2000),
        clock.SyntheticClockSample(2, _SOURCE, 1001, 2001),
    ]


def _clone_integer(value):
    replacement = int(str(value))
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize("field", ("wall_ms", "monotonic_ns"))
def test_prior_sample_equal_numeric_replacement_is_rejected(field):
    samples = _samples()

    def injected():
        yield samples[0]
        object.__setattr__(
            samples[0], field, _clone_integer(getattr(samples[0], field)),
        )
        yield samples[1]

    with pytest.raises(clock.SyntheticClockRejected, match="prior clock sample changed"):
        clock.review_synthetic_clock_sequence(injected())


@pytest.mark.parametrize("field", ("last_wall_ms", "last_monotonic_ns"))
def test_retained_witness_numeric_carrier_replaced_during_validation(
    monkeypatch, field,
):
    samples = _samples()
    retained = clock.review_synthetic_clock_sequence(samples[:1])
    previous = clock._check_witness

    def mutate_after_validation(value):
        previous(value)
        object.__setattr__(value, field, _clone_integer(getattr(value, field)))

    monkeypatch.setattr(clock, "_check_witness", mutate_after_validation)
    with pytest.raises(clock.SyntheticClockRejected, match="retained clock witness changed"):
        clock.review_synthetic_clock_sequence(samples, retained=retained)


@pytest.mark.parametrize("field", ("last_wall_ms", "last_monotonic_ns"))
def test_constructed_clock_link_cannot_replace_equal_numeric_carrier(
    monkeypatch, field,
):
    previous = clock.SyntheticClockWitness.__init__

    def mutate_after_construction(self, *args, **kwargs):
        previous(self, *args, **kwargs)
        if self.event_count == 1:
            object.__setattr__(self, field, _clone_integer(getattr(self, field)))

    monkeypatch.setattr(
        clock.SyntheticClockWitness, "__init__", mutate_after_construction,
    )
    with pytest.raises(clock.SyntheticClockRejected, match="constructed clock chain link"):
        clock.review_synthetic_clock_sequence(_samples())


def test_unmodified_numeric_carriers_preserve_retained_prefix():
    samples = _samples()
    first = clock.review_synthetic_clock_sequence(samples[:1])
    continued = clock.review_synthetic_clock_sequence(samples, retained=first)
    assert continued.event_count == 2
    assert continued.chain_hash != first.chain_hash
    assert continued.trusted_clock_verified is False
    assert continued.dispatch_authorized is False
    assert continued.automatic_replay_authorized is False
