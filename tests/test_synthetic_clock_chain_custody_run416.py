"""Synthetic clock link callbacks must never rewrite a prior chain result."""

import hashlib
import sys

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def _sample(seq):
    return clock.SyntheticClockSample(
        seq, hashlib.sha256(b"offline-fixture").hexdigest(), seq, seq,
    )


@pytest.mark.parametrize("target_step", (1, 2))
def test_hash_callback_cannot_reflectively_rewrite_prior_clock_link(
    monkeypatch, target_step,
):
    original_hash = clock._hash
    callbacks = 0

    def malicious_hash(domain, fields):
        nonlocal callbacks
        if domain == "ARK-disconnected-clock-event-v1":
            callbacks += 1
            if callbacks == target_step:
                previous = sys._getframe(1).f_locals["prior"]
                object.__setattr__(
                    previous, "chain_hash", "clk_" + "f" * 64,
                )
        return original_hash(domain, fields)

    monkeypatch.setattr(clock, "_hash", malicious_hash)
    with pytest.raises(clock.SyntheticClockRejected, match="prior clock chain link"):
        clock.review_synthetic_clock_sequence((_sample(1), _sample(2)))
    assert callbacks == target_step


@pytest.mark.parametrize("bad_hash", ("not-a-hash", None, 1, "clk_" + "F" * 64))
def test_hash_callback_must_produce_bounded_canonical_event_digest(
    monkeypatch, bad_hash,
):
    original_hash = clock._hash

    def invalid_hash(domain, fields):
        if domain == "ARK-disconnected-clock-event-v1":
            return bad_hash
        return original_hash(domain, fields)

    monkeypatch.setattr(clock, "_hash", invalid_hash)
    with pytest.raises(clock.SyntheticClockRejected, match="event digest"):
        clock.review_synthetic_clock_sequence((_sample(1),))


def test_synthetic_clock_still_supports_retained_extension_without_authority():
    prefix = clock.review_synthetic_clock_sequence((_sample(1),))
    extended = clock.review_synthetic_clock_sequence(
        (_sample(1), _sample(2)), retained=prefix,
    )
    assert extended.event_count == 2
    assert extended.source_digest == prefix.source_digest
    assert not extended.trusted_clock_verified
    assert not extended.dispatch_authorized
    assert not extended.automatic_replay_authorized
