"""Hash callback custody across explicit, disconnected fixture ingestion.

All payloads are synthetic caller-provided in-memory bytes. No acquisition,
model dispatch, authentication, consent or live external action is performed.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.observation_fixture_adapters as mod
from ark.observations import ObservationKind


@pytest.mark.parametrize("kind", (
    ObservationKind.TEXT, ObservationKind.TRANSCRIPT,
    ObservationKind.IMAGE, ObservationKind.SCREEN,
))
def test_metadata_preflight_callback_cannot_redirect_private_bytes(
    monkeypatch, kind,
):
    payload = b"synthetic private bytes not sent to injected function"
    original_preflight = mod._preflight_fixture_metadata
    calls = []

    def hostile_hash(_payload=b""):
        calls.append("rogue SHA callback received private bytes")
        raise AssertionError("hostile SHA received observation payload")

    def reentrant_preflight(*args):
        original_preflight(*args)
        monkeypatch.setattr(mod.hashlib, "sha256", hostile_hash)

    monkeypatch.setattr(mod, "_preflight_fixture_metadata", reentrant_preflight)
    kwargs = {
        "kind": kind, "source_id": "fixture-source",
        "privacy_scope": "synthetic-only", "ingested_at_ms": 42,
    }
    with pytest.raises(ValueError, match="digest implementation changed"):
        if kind in (ObservationKind.TEXT, ObservationKind.TRANSCRIPT):
            mod.fixture_text_observation(payload.decode("ascii"), **kwargs)
        else:
            mod.fixture_binary_observation(payload, **kwargs)
    assert calls == []


@pytest.mark.parametrize("kind", (
    ObservationKind.TEXT, ObservationKind.TRANSCRIPT,
    ObservationKind.IMAGE, ObservationKind.SCREEN,
))
def test_original_digest_still_hashes_exact_payload_and_grants_nothing(kind):
    payload = b"synthetic payload for exact-content hashing"
    kwargs = {
        "kind": kind, "source_id": "fixture-source",
        "privacy_scope": "synthetic-only", "ingested_at_ms": 42,
    }
    if kind in (ObservationKind.TEXT, ObservationKind.TRANSCRIPT):
        envelope = mod.fixture_text_observation(payload.decode("ascii"), **kwargs)
    else:
        envelope = mod.fixture_binary_observation(payload, **kwargs)
    assert envelope.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert envelope.kind is kind
    assert envelope.source_id == "fixture-source"
    assert envelope.privacy_scope == "synthetic-only"
    assert repr(envelope).find("synthetic payload") == -1
