"""Offline observation fixtures reject mutable envelope validators and slots.

Only provided synthetic in-memory content is handled; no device, microphone,
camera, network or real ToolBackend is accessed by these regressions.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationEnvelope, ObservationKind


def _text():
    return adapters.fixture_text_observation(
        "synthetic private transcript", kind=ObservationKind.TRANSCRIPT,
        source_id="local-source", privacy_scope="local-only",
        ingested_at_ms=123,
    )


@pytest.mark.parametrize("name", [
    "__post_init__", "source_id", "content_sha256", "privacy_scope",
    "schema_version", "__getattribute__", "__getattr__",
])
def test_preinstalled_executable_envelope_field_or_validator_never_runs(
    monkeypatch, name,
):
    invoked = []

    def forbidden(*_args):
        invoked.append(name)
        raise AssertionError("forged envelope hook must not run")

    with monkeypatch.context() as patch:
        if name.startswith("__"):
            patch.setattr(ObservationEnvelope, name, forbidden, raising=False)
        else:
            patch.setattr(ObservationEnvelope, name, property(forbidden))
        with pytest.raises(ValueError, match="definition changed"):
            _text()
    assert invoked == []


@pytest.mark.parametrize("name", [
    "__post_init__", "content_sha256",
])
def test_reentrant_hash_is_refused_before_executable_accessor_installation(
    monkeypatch, name,
):
    called = []
    digest_called = []
    original = hashlib.sha256

    def forbidden(*_args):
        called.append(name)
        raise AssertionError("never invoke injected validator or accessor")

    with monkeypatch.context() as patch:
        def mutate(digest_input=b"", *args, **kwargs):
            digest_called.append(True)
            patch.setattr(
                ObservationEnvelope, name,
                forbidden if name.startswith("__") else property(forbidden),
            )
            return original(digest_input, *args, **kwargs)

        patch.setattr(
            adapters, "hashlib", SimpleNamespace(sha256=mutate),
        )
        with pytest.raises(ValueError, match="digest implementation changed"):
            _text()
    assert called == []
    assert digest_called == []


def test_normal_local_observation_remains_minimal_and_inert():
    envelope = _text()
    assert envelope.kind is ObservationKind.TRANSCRIPT
    assert envelope.privacy_scope == "local-only"
    assert envelope.content_sha256 == hashlib.sha256(
        b"synthetic private transcript",
    ).hexdigest()
    assert "synthetic private transcript" not in repr(envelope)
