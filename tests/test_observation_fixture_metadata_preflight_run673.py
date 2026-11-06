"""Disconnected fixture metadata is checked before hashing private payloads.

No device acquisition or external tools. Input shape checks grant no consent,
provenance, dispatch or automatic replay authority.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.observation_fixture_adapters as fixtures
from ark.observations import ObservationKind


@pytest.mark.parametrize("binary", (False, True))
@pytest.mark.parametrize(
    ("label", "value", "diagnostic"),
    (
        ("source_id", " ", "non-empty exact"),
        ("privacy_scope", "", "non-empty exact"),
        ("source_id", "é" * 513, "identifier budget"),
        ("privacy_scope", "あ" * 342, "identifier budget"),
        ("source_id", "broken\ud800", "valid UTF-8"),
        ("privacy_scope", "broken\udfff", "valid UTF-8"),
        ("ingested_at_ms", True, "exact integer"),
        ("ingested_at_ms", 2**63, "exact integer"),
        ("parent_sha256", "A" * 64, "lowercase SHA-256"),
        ("parent_sha256", 0, "lowercase SHA-256"),
    ),
)
def test_invalid_metadata_never_reaches_private_content_hash(
    monkeypatch, binary, label, value, diagnostic,
):
    def forbidden_hash(_payload):
        pytest.fail("malformed metadata reached caller-private content hashing")

    monkeypatch.setattr(fixtures.hashlib, "sha256", forbidden_hash)
    args = {
        "kind": ObservationKind.IMAGE if binary else ObservationKind.TEXT,
        "source_id": "local-fixture",
        "privacy_scope": "private:fixture",
        "ingested_at_ms": 10,
    }
    args[label] = value
    with pytest.raises(ValueError, match=diagnostic):
        if binary:
            fixtures.fixture_binary_observation(b"private binary bytes", **args)
        else:
            fixtures.fixture_text_observation("private fixture text", **args)


@pytest.mark.parametrize("binary", (False, True))
def test_exact_1024_byte_labels_and_valid_parent_preserve_byte_identity(binary):
    content = b"fixture bytes" if binary else "fixture text"
    parent = "a" * 64
    args = {
        "kind": ObservationKind.SCREEN if binary else ObservationKind.TRANSCRIPT,
        "source_id": "é" * 512,
        "privacy_scope": "あ" * 341 + "a",
        "ingested_at_ms": 10,
        "parent_sha256": parent,
    }
    if binary:
        result = fixtures.fixture_binary_observation(content, **args)
        data = content
    else:
        result = fixtures.fixture_text_observation(content, **args)
        data = content.encode("utf-8")
    assert len(args["source_id"].encode()) == 1024
    assert len(args["privacy_scope"].encode()) == 1024
    assert result.content_sha256 == hashlib.sha256(data).hexdigest()
    assert result.parent_sha256 == parent
    assert not hasattr(result, "raw_bytes")
    assert not hasattr(result, "payload")
