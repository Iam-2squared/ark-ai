"""Disconnected clock chain rejects substituted local hash/JSON identity.

Caller-supplied timestamps are not trusted time. These tests never inspect
hardware, send notifications, consume approvals, or execute real tools.
"""

from __future__ import annotations

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def _sample() -> clock.SyntheticClockSample:
    return clock.SyntheticClockSample(1, "a" * 64, 100, 200)


@pytest.mark.parametrize(
    "mutation",
    ("sha256", "dumps", "hashlib_module", "json_module", "genesis_equal"),
)
def test_digest_substitution_fails_before_hash_or_iterator(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    inspected = []

    def forbidden(*_args, **_kwargs):
        inspected.append(True)
        raise AssertionError("counterfeit hash or JSON callback executed")

    def input_stream():
        inspected.append("iterator")
        yield _sample()

    with monkeypatch.context() as patch:
        if mutation == "sha256":
            patch.setattr(clock.hashlib, "sha256", forbidden)
        elif mutation == "dumps":
            patch.setattr(clock.json, "dumps", forbidden)
        elif mutation == "hashlib_module":
            patch.setattr(clock, "hashlib", object())
        elif mutation == "json_module":
            patch.setattr(clock, "json", object())
        else:
            original = clock._GENESIS
            alternate = ("!" + original)[1:]
            assert alternate == original and alternate is not original
            patch.setattr(clock, "_GENESIS", alternate)
        with pytest.raises(
            clock.SyntheticClockRejected,
            match="synthetic clock digest implementation changed",
        ):
            clock.review_synthetic_clock_sequence(input_stream())
    assert inspected == []


@pytest.mark.parametrize("mutation", ("sha256", "dumps"))
def test_hash_callback_replacement_is_rejected_before_first_hash(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    native = clock._hash
    called = []

    def forged(*_args, **_kwargs):
        raise AssertionError("substituted implementation invoked on later hash")

    def switch_after_hash(*args, **kwargs):
        result = native(*args, **kwargs)
        called.append(True)
        if mutation == "sha256":
            monkeypatch.setattr(clock.hashlib, "sha256", forged)
        else:
            monkeypatch.setattr(clock.json, "dumps", forged)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(clock, "_hash", switch_after_hash)
        with pytest.raises(
            clock.SyntheticClockRejected,
            match="synthetic clock digest implementation changed",
        ):
            clock.review_synthetic_clock_sequence((_sample(),))
    # The pinned helper rejects injection before switch_after_hash can execute.
    # This early refusal is stronger than the prior post-hash rejection.
    assert called == []


def test_original_local_chain_stays_non_authorizing() -> None:
    original = clock.review_synthetic_clock_sequence((_sample(),))
    assert original.event_count == 1
    assert original.last_wall_ms == 100
    assert original.last_monotonic_ns == 200
    assert original.trusted_clock_verified is False
    assert original.dispatch_authorized is False
    assert original.automatic_replay_authorized is False
