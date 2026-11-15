"""Run905: observation fixture label budgets precede whitespace allocation.

Only caller-provided synthetic bytes are used. No devices, media or tools.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import observation_fixture_adapters as mod
from ark.observations import ObservationKind


@pytest.mark.parametrize("binary", [False, True])
@pytest.mark.parametrize("label", ["source_id", "privacy_scope"])
@pytest.mark.parametrize("oversize", [
    " " * 100_000,
    "x" * 100_000,
    "\x00" + "x" * 100_000,
])
def test_oversize_label_rejected_before_private_hash(
    monkeypatch, binary, label, oversize,
):
    def forbidden(_payload):
        pytest.fail("private fixture bytes reached a digest callback")

    monkeypatch.setattr(mod, "_hash_private_fixture", forbidden)
    kwargs = {
        "source_id": "local:fixture",
        "privacy_scope": "local:private",
        "ingested_at_ms": 42,
    }
    kwargs[label] = oversize
    with pytest.raises(ValueError, match="identifier budget"):
        if binary:
            mod.fixture_binary_observation(
                b"private disconnected fixture",
                kind=ObservationKind.IMAGE, **kwargs,
            )
        else:
            mod.fixture_text_observation(
                "private disconnected fixture",
                kind=ObservationKind.TEXT, **kwargs,
            )


def test_valid_1024_byte_label_preserves_digest_only_output():
    observed = mod.fixture_text_observation(
        "detached synthetic text",
        kind=ObservationKind.TRANSCRIPT,
        source_id="é" * 512,
        privacy_scope="local:private",
        ingested_at_ms=42,
    )
    assert observed.content_sha256 == hashlib.sha256(
        b"detached synthetic text"
    ).hexdigest()
    assert observed.source_id == "é" * 512
    assert not hasattr(observed, "raw_bytes")
