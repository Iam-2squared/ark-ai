"""Offline observation hashing must not invoke a substituted private helper.

Synthetic in-memory text/binary payloads only. No device acquisition,
filesystem observation, credentials, approval, or ToolBackend dispatch.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


def _adapt(kind: ObservationKind):
    content = b"synthetic local payload not accessible to untrusted callbacks"
    kwargs = {
        "kind": kind,
        "source_id": "disconnected-fixture",
        "privacy_scope": "private-only",
        "ingested_at_ms": 77,
    }
    if kind in (ObservationKind.TEXT, ObservationKind.TRANSCRIPT):
        return adapters.fixture_text_observation(content.decode("ascii"), **kwargs)
    return adapters.fixture_binary_observation(content, **kwargs)


@pytest.mark.parametrize(
    "kind",
    (
        ObservationKind.TEXT, ObservationKind.TRANSCRIPT,
        ObservationKind.IMAGE, ObservationKind.SCREEN,
    ),
)
def test_replaced_private_hash_helper_never_receives_raw_data(
    monkeypatch, kind: ObservationKind,
) -> None:
    touched = []

    def hostile(payload):
        touched.append(payload)
        raise AssertionError("hostile local helper received private fixture bytes")

    monkeypatch.setattr(adapters, "_hash_private_fixture", hostile)
    with pytest.raises(ValueError, match="private digest helper changed"):
        _adapt(kind)
    assert touched == []


@pytest.mark.parametrize(
    "kind",
    (
        ObservationKind.TEXT, ObservationKind.TRANSCRIPT,
        ObservationKind.IMAGE, ObservationKind.SCREEN,
    ),
)
def test_unmodified_private_digest_helper_keeps_original_minimization(
    kind: ObservationKind,
) -> None:
    envelope = _adapt(kind)
    content = b"synthetic local payload not accessible to untrusted callbacks"
    assert envelope.kind is kind
    assert envelope.content_sha256 == hashlib.sha256(content).hexdigest()
    assert envelope.privacy_scope == "private-only"
    assert not hasattr(envelope, "payload")
    assert not hasattr(envelope, "content")
    assert content.decode("ascii") not in repr(envelope)
