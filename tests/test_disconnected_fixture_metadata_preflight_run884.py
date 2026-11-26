"""Metadata preflight for the synthetic, disconnected observation fixture.

Synthetic in-memory bytes only. No live sensor, network, model or tool action.
"""

import hashlib
import sys
from collections.abc import Callable

import pytest

from ark import disconnected_observation_fixture as fixture
from ark.observations import ObservationKind


def _make(**overrides: object) -> object:
    inputs: dict[str, object] = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "privacy_scope": "local-private",
        "ingested_at_ms": 0,
        "payload": b"private synthetic payload",
    }
    inputs.update(overrides)
    return fixture.make_disconnected_fixture(**inputs)  # type: ignore[arg-type]


def _run_counting_hashes(callback: Callable[[], object]) -> list[object]:
    """Record only actual SHA-256 C calls directly from fixture execution."""
    observed: list[object] = []
    previous = sys.getprofile()

    def profiler(frame: object, event: str, arg: object) -> None:
        if (
            event == "c_call"
            and getattr(frame, "f_code", None)
            is fixture.make_disconnected_fixture.__code__
            and arg is hashlib.sha256
        ):
            observed.append(arg)

    sys.setprofile(profiler)
    try:
        callback()
    finally:
        sys.setprofile(previous)
    return observed


@pytest.mark.parametrize(
    ("updates", "error"),
    (
        ({"source_id": ""}, "non-empty"),
        ({"source_id": "x" * 1025}, "identifier budget"),
        ({"source_id": "🪐" * 257}, "identifier budget"),
        ({"privacy_scope": "bad\ud800"}, "valid UTF-8"),
        ({"privacy_scope": False}, "non-empty"),
        ({"ingested_at_ms": True}, "non-negative exact integer"),
        ({"ingested_at_ms": -1}, "non-negative exact integer"),
        ({"ingested_at_ms": 2**63}, "non-negative exact integer"),
        ({"parent_sha256": "a" * 65}, "lowercase SHA-256"),
        ({"parent_sha256": "Z" * 64}, "lowercase SHA-256"),
    ),
)
def test_invalid_metadata_rejected_before_payload_digest(
    updates: dict[str, object], error: str,
) -> None:
    def rejected() -> None:
        with pytest.raises((ValueError, TypeError), match=error):
            _make(**updates)

    assert _run_counting_hashes(rejected) == []


def test_valid_parent_and_budget_metadata_yield_one_digest() -> None:
    payload = b"purely synthetic bytes"
    observed = _run_counting_hashes(
        lambda: _make(
            payload=payload,
            source_id="🪐" * 256,
            parent_sha256="b" * 64,
            ingested_at_ms=2**63 - 1,
        ),
    )
    assert len(observed) == 1
    result = _make(payload=payload, parent_sha256="b" * 64)
    assert result.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert result.parent_sha256 == "b" * 64
    assert not hasattr(result, "payload")
