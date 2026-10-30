"""Pinned local Observation v1 validation cannot be bypassed by constructor hooks."""

from __future__ import annotations

import pytest

from ark.observation_fixture_adapters import (
    fixture_binary_observation,
    fixture_text_observation,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _text(**overrides):
    options = {
        "kind": ObservationKind.TEXT,
        "source_id": "fixture",
        "privacy_scope": "offline:test",
        "ingested_at_ms": 100,
    }
    options.update(overrides)
    return fixture_text_observation("synthetic only", **options)


def _binary(**overrides):
    options = {
        "kind": ObservationKind.SCREEN,
        "source_id": "fixture",
        "privacy_scope": "offline:test",
        "ingested_at_ms": 100,
    }
    options.update(overrides)
    return fixture_binary_observation(b"synthetic bytes", **options)


def test_unmodified_fixture_still_roundtrips():
    text = _text()
    binary = _binary()
    assert type(text) is ObservationEnvelope
    assert type(binary) is ObservationEnvelope
    assert text.kind is ObservationKind.TEXT
    assert binary.kind is ObservationKind.SCREEN
    assert text.content_sha256 != binary.content_sha256


@pytest.mark.parametrize("broken,fragment", [
    ({"source_id": ""}, "source_id"),
    ({"privacy_scope": ""}, "privacy_scope"),
    ({"ingested_at_ms": True}, "ingested_at_ms"),
    ({"parent_sha256": "not-a-sha"}, "parent_sha256"),
    ({"source_id": "x" * 1025}, "identifier budget"),
])
def test_injected_noop_post_init_cannot_admit_invalid_text(
    monkeypatch, broken, fragment,
):
    monkeypatch.setattr(ObservationEnvelope, "__post_init__", lambda self: None)
    with pytest.raises(ValueError, match=fragment):
        _text(**broken)


@pytest.mark.parametrize("broken,fragment", [
    ({"source_id": ""}, "source_id"),
    ({"ingested_at_ms": -1}, "ingested_at_ms"),
    ({"parent_sha256": "A" * 64}, "parent_sha256"),
])
def test_injected_noop_post_init_cannot_admit_invalid_binary(
    monkeypatch, broken, fragment,
):
    monkeypatch.setattr(ObservationEnvelope, "__post_init__", lambda self: None)
    with pytest.raises(ValueError, match=fragment):
        _binary(**broken)
