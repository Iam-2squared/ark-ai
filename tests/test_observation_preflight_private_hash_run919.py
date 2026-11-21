"""Malformed observation fixture metadata must not reach private hashing.

Only in-memory synthetic text and bytes are supplied. No camera, microphone,
screen, file acquisition, consent or external action is available.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


@pytest.mark.parametrize("modality", ("text", "binary"))
@pytest.mark.parametrize(
    "change",
    (
        {"source_id": "日" * 342},
        {"privacy_scope": "private\x00native"},
        {"ingested_at_ms": True},
        {"parent_sha256": "F" * 64},
        {"source_id": "\ud800"},
    ),
)
def test_invalid_metadata_rejected_before_any_private_hasher(
    monkeypatch, modality, change,
):
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("HASHED")
        raise AssertionError("private payload must not reach substituted hasher")

    defaults = dict(
        source_id="synthetic-source",
        privacy_scope="synthetic-private",
        ingested_at_ms=100,
        parent_sha256=None,
    )
    defaults.update(change)
    with monkeypatch.context() as patch:
        patch.setattr(adapters, "_hash_private_fixture", forbidden)
        with pytest.raises(ValueError):
            if modality == "text":
                adapters.fixture_text_observation(
                    "synthetic secret fixture only",
                    kind=ObservationKind.TEXT,
                    **defaults,
                )
            else:
                adapters.fixture_binary_observation(
                    b"synthetic secret fixture only",
                    kind=ObservationKind.IMAGE,
                    **defaults,
                )
    assert calls == []


def test_valid_synthetic_text_is_only_represented_by_digest():
    private_fixture = "synthetic text, never acquired from a user"
    envelope = adapters.fixture_text_observation(
        private_fixture,
        kind=ObservationKind.TEXT,
        source_id="synthetic-source",
        privacy_scope="offline-private",
        ingested_at_ms=100,
    )
    assert envelope.content_sha256 == hashlib.sha256(
        private_fixture.encode("utf-8")
    ).hexdigest()
    assert private_fixture not in repr(envelope)
    assert envelope.observation_id.startswith("obs_")
