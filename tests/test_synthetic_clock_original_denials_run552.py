"""A passive clock proof cannot be upgraded by substituting False getters."""

import hashlib

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def sample():
    return clock.SyntheticClockSample(
        1, hashlib.sha256(b"local-fixture").hexdigest(), 100, 101,
    )


@pytest.mark.parametrize(
    "flag", (
        "trusted_clock_verified", "dispatch_authorized",
        "automatic_replay_authorized",
    ),
)
def test_preinstalled_false_only_denial_rejected_before_iterator(
    monkeypatch, flag,
):
    yielded = []

    def samples():
        yielded.append(True)
        yield sample()

    monkeypatch.setattr(
        clock.SyntheticClockWitness, flag, property(lambda self: False),
    )
    with pytest.raises(clock.SyntheticClockRejected, match="descriptor changed"):
        clock.review_synthetic_clock_sequence(samples())
    assert not yielded


def test_reentrant_digest_callback_cannot_replace_original_denial(monkeypatch):
    original = clock._hash
    changed = []

    def swap(domain, fields):
        value = original(domain, fields)
        if domain == "ARK-disconnected-clock-event-v1":
            monkeypatch.setattr(
                clock.SyntheticClockWitness,
                "automatic_replay_authorized",
                property(lambda self: False),
            )
            changed.append(True)
        return value

    monkeypatch.setattr(clock, "_hash", swap)
    with pytest.raises(clock.SyntheticClockRejected, match="digest implementation changed"):
        clock.review_synthetic_clock_sequence((sample(),))
    # The replacement digest callback is rejected at ingress: it must never
    # get a chance to install a counterfeit False-only authority property.
    assert changed == []


def test_original_clock_denials_preserve_inert_local_witness():
    value = clock.review_synthetic_clock_sequence((sample(),))
    assert value.event_count == 1
    assert value.trusted_clock_verified is False
    assert value.dispatch_authorized is False
    assert value.automatic_replay_authorized is False
