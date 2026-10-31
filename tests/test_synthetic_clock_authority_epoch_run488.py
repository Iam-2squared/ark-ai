"""Synthetic time digests cannot acquire dispatch, replay or trusted-clock rights."""

from __future__ import annotations

import hashlib

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def _sample():
    return clock.SyntheticClockSample(
        1, hashlib.sha256(b"untrusted-clock-source").hexdigest(), 100, 1_000,
    )


@pytest.mark.parametrize("field", [
    "trusted_clock_verified",
    "dispatch_authorized",
    "automatic_replay_authorized",
])
def test_generator_completion_cannot_upgrade_last_witness_authority(
    monkeypatch, field,
):
    def samples():
        yield _sample()
        # The previously constructed witness was validated already.
        # An adversarial generator changes a class descriptor on completion.
        monkeypatch.setattr(
            clock.SyntheticClockWitness, field, property(lambda _self: True),
        )

    with pytest.raises(
        clock.SyntheticClockRejected,
        match="constructed clock witness changed",
    ):
        clock.review_synthetic_clock_sequence(samples())


@pytest.mark.parametrize("field", [
    "trusted_clock_verified",
    "dispatch_authorized",
    "automatic_replay_authorized",
])
def test_retained_clock_witness_with_upgraded_authority_is_rejected(
    monkeypatch, field,
):
    sample = _sample()
    retained = clock.review_synthetic_clock_sequence((sample,))
    monkeypatch.setattr(
        clock.SyntheticClockWitness, field, property(lambda _self: True),
    )
    with pytest.raises(
        clock.SyntheticClockRejected, match="invalid synthetic clock witness",
    ):
        clock.review_synthetic_clock_sequence((sample,), retained=retained)


def test_unchanged_local_clock_witness_is_still_not_trusted():
    result = clock.review_synthetic_clock_sequence((_sample(),))
    assert result.trusted_clock_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
