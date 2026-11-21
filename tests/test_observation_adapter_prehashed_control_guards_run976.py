"""Opt-in observation adapters reject ambiguous labels before private hashing.

The frozen public ObservationEnvelope v1 contract is unchanged. These fixture
adapters acquire no sensors or files and grant no provenance/consent/dispatch.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.observation_fixture_adapters as adapters
from ark.observations import ObservationKind


@pytest.mark.parametrize(
    ("control", "diagnostic"),
    (
        ("\t", "ASCII control"),
        ("\n", "ASCII control"),
        ("\x7f", "ASCII control"),
        ("\u009b", "Unicode formatting control"),
        ("\u202e", "Unicode formatting control"),
        ("\u200b", "Unicode formatting control"),
        ("\u2028", "Unicode formatting control"),
        ("\ufeff", "Unicode formatting control"),
    ),
)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
@pytest.mark.parametrize("binary", (False, True))
def test_controlled_identity_is_rejected_before_private_hash(
    monkeypatch, control: str, diagnostic: str, field: str, binary: bool,
) -> None:
    touched: list[bytes] = []

    def forbidden_hash(payload: bytes) -> str:
        touched.append(payload)
        raise AssertionError("invalid label reached private hashing")

    monkeypatch.setattr(adapters, "_hash_private_fixture", forbidden_hash)
    args = {
        "kind": ObservationKind.IMAGE if binary else ObservationKind.TEXT,
        "source_id": "synthetic/観測",
        "privacy_scope": "local:非公開",
        "ingested_at_ms": 24,
    }
    args[field] += control + "forged"
    with pytest.raises(ValueError, match=diagnostic):
        if binary:
            adapters.fixture_binary_observation(b"private synthetic bytes", **args)
        else:
            adapters.fixture_text_observation("private synthetic text", **args)
    assert touched == []


@pytest.mark.parametrize("binary", (False, True))
def test_multilingual_clean_fixture_remains_digest_only(binary: bool) -> None:
    raw = b"synthetic" if binary else "合成資料🧪"
    args = {
        "kind": ObservationKind.SCREEN if binary else ObservationKind.TRANSCRIPT,
        "source_id": "東京/観測",
        "privacy_scope": "local:非公開",
        "ingested_at_ms": 24,
    }
    if binary:
        result = adapters.fixture_binary_observation(raw, **args)
        expected = raw
    else:
        result = adapters.fixture_text_observation(raw, **args)
        expected = raw.encode("utf-8")
    assert result.content_sha256 == hashlib.sha256(expected).hexdigest()
    assert result.adapter_id.startswith("fixture:")
    assert result.schema_version == 1
    assert not hasattr(result, "raw_bytes")
    assert not hasattr(result, "payload")
