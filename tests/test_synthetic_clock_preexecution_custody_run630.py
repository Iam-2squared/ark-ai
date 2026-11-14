"""Run630: untrusted synthetic clock carriers never execute replaced hooks.

These are local mock timestamps, not authenticated time or tool authority.
"""

from __future__ import annotations

import pytest

from ark.agency import synthetic_clock_sequence_review as clock

_SOURCE = "a" * 64


def _sample(index: int) -> clock.SyntheticClockSample:
    return clock.SyntheticClockSample(
        index, _SOURCE, 1000 + index, 2000 + index,
    )


@pytest.mark.parametrize(("carrier", "attribute"), [
    ("sample", "__init__"),
    ("sample", "__getattribute__"),
    ("sample", "source_digest"),
    ("sample", "monotonic_ns"),
    ("witness", "__init__"),
    ("witness", "__getattribute__"),
    ("witness", "chain_hash"),
    ("witness", "trusted_clock_verified"),
])
def test_preinstalled_clock_carrier_is_never_invoked(
    monkeypatch: pytest.MonkeyPatch, carrier: str, attribute: str,
) -> None:
    sample = _sample(1)
    invoked: list[str] = []

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append(attribute)
        raise AssertionError("malicious clock carrier was executed")

    cls = (
        clock.SyntheticClockSample
        if carrier == "sample"
        else clock.SyntheticClockWitness
    )
    monkeypatch.setattr(cls, attribute, poisoned, raising=False)
    with pytest.raises(clock.SyntheticClockRejected, match="descriptor changed"):
        clock.review_synthetic_clock_sequence((sample,))
    assert invoked == []


def test_reentrant_hash_must_not_invoke_late_witness_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = _sample(1)
    original_hash = clock._hash
    original_init = clock.SyntheticClockWitness.__init__
    invoked: list[str] = []

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append("init")
        raise AssertionError("late witness initializer executed")

    def callback(domain: str, fields: object) -> str:
        value = original_hash(domain, fields)
        if domain == "ARK-disconnected-clock-event-v1":
            monkeypatch.setattr(
                clock.SyntheticClockWitness, "__init__", poisoned,
            )
        return value

    monkeypatch.setattr(clock, "_hash", callback)
    try:
        with pytest.raises(
            clock.SyntheticClockRejected, match="digest implementation changed",
        ):
            clock.review_synthetic_clock_sequence((sample,))
        # The replaced hash itself is refused before it can poison __init__.
        assert invoked == []
    finally:
        monkeypatch.setattr(clock.SyntheticClockWitness, "__init__", original_init)


def test_late_sample_descriptor_swap_rejected_before_second_yield(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[str] = []

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append("sample")
        raise AssertionError("changed sample hook executed")

    second = _sample(2)

    def input_samples():
        yield _sample(1)
        monkeypatch.setattr(
            clock.SyntheticClockSample, "__getattribute__", poisoned,
        )
        yield second

    with pytest.raises(clock.SyntheticClockRejected, match="descriptor changed"):
        clock.review_synthetic_clock_sequence(input_samples())
    assert invoked == []


def test_normal_clock_chain_remains_non_authorizing() -> None:
    result = clock.review_synthetic_clock_sequence((_sample(1), _sample(2)))
    assert result.event_count == 2
    assert result.trusted_clock_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
