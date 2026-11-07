"""Offline Personal Context must not accept serializer-retargeted fixture JSON."""

from __future__ import annotations

import hashlib
import json

import pytest

import ark.personal_context_offline_preview as mod

OWNER = "a" * 64
SCOPE = "b" * 64


def _fixture(content="private text"):
    return mod.OfflineContextFixture(
        "rec_" + "1" * 32,
        OWNER, SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 1000,
    )


def _preview(record):
    return mod.build_offline_context_preview(
        (record,), owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,), observed_at_ms=100,
    )


def test_clean_canonical_fixture_roundtrip_is_deterministic():
    record = _fixture("日本語 fixture")
    first = _preview(record)
    again = _preview(record)
    assert first == again
    parsed = json.loads(first.canonical_local_json)
    assert parsed["owner_digest"] == OWNER
    assert parsed["records"][0]["content"] == "日本語 fixture"
    assert first.external_export_authorized is False
    assert first.consent_verified is False


def test_valid_but_retargeted_json_is_rejected(monkeypatch):
    original = mod.json.dumps
    calls = []

    def retarget(data, **kwargs):
        encoded = original(data, **kwargs)
        calls.append(True)
        if len(calls) == 1:
            return encoded.replace("private text", "disclosed text")
        return encoded

    monkeypatch.setattr(mod.json, "dumps", retarget)
    with pytest.raises(mod.OfflineContextPreviewRejected, match="disagrees"):
        _preview(_fixture())


def test_serializer_cannot_replace_owner_digest(monkeypatch):
    original = mod.json.dumps

    def retarget(data, **kwargs):
        return original(data, **kwargs).replace(OWNER, "c" * 64)

    monkeypatch.setattr(mod.json, "dumps", retarget)
    with pytest.raises(mod.OfflineContextPreviewRejected, match="disagrees"):
        _preview(_fixture())


def test_invalid_serialized_json_fails_closed(monkeypatch):
    monkeypatch.setattr(mod.json, "dumps", lambda *a, **k: "{not-json")
    with pytest.raises(mod.OfflineContextPreviewRejected, match="serialization invalid"):
        _preview(_fixture())


def test_noncanonical_but_equivalent_json_fails_closed(monkeypatch):
    original = mod.json.dumps
    counter = []

    def extra_whitespace(data, **kwargs):
        result = original(data, **kwargs)
        counter.append(1)
        if len(counter) == 1:
            return result + " "
        return result

    monkeypatch.setattr(mod.json, "dumps", extra_whitespace)
    with pytest.raises(mod.OfflineContextPreviewRejected, match="not canonical"):
        _preview(_fixture())


def test_parser_must_return_exact_json_object(monkeypatch):
    monkeypatch.setattr(mod.json, "loads", lambda text: 123)
    with pytest.raises(mod.OfflineContextPreviewRejected, match="disagrees"):
        _preview(_fixture())


def test_parser_callback_cannot_retarget_original_record(monkeypatch):
    record = _fixture()
    original = mod.json.loads

    def mutate(text):
        result = original(text)
        object.__setattr__(record, "content", "other content")
        return result

    monkeypatch.setattr(mod.json, "loads", mutate)
    with pytest.raises(mod.OfflineContextPreviewRejected, match="changed"):
        _preview(record)
