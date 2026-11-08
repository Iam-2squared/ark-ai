"""Offline private masking receipts bind reviewed fields to canonical JSON."""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_redaction as redaction


def _preview():
    source = "private fixture data"
    return redaction.preview_offline_redaction(
        source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, len(source), "SECRET"),),
    )


def test_unmodified_complete_mask_is_deterministic_and_non_authorizing():
    one = _preview()
    assert _preview() == one
    assert one.masked_text == "[MASK:SECRET]"
    assert one.complete_masking is True
    assert one.external_export_authorized is False
    assert one.privacy_erasure_proven is False


@pytest.mark.parametrize("field", ["owner", "scope", "source", "result", "mask"])
def test_forged_canonical_serializer_payload_is_not_digest_evidence(
    monkeypatch, field,
):
    original = redaction.json.dumps

    def forged(data, **kwargs):
        altered = dict(data)
        altered[field] = (
            [[0, 1, "SECRET"]] if field == "mask" else "forged-output"
        )
        return original(altered, **kwargs)

    monkeypatch.setattr(redaction.json, "dumps", forged)
    with pytest.raises(
        redaction.OfflineRedactionRejected,
        match="masked preview authority definition changed",
    ):
        _preview()


def test_noncanonical_whitespace_is_refused_even_when_payload_agrees(
    monkeypatch,
):
    original = redaction.json.dumps

    def spaced(data, **kwargs):
        return original(data, **kwargs) + " "

    monkeypatch.setattr(redaction.json, "dumps", spaced)
    with pytest.raises(
        redaction.OfflineRedactionRejected,
        match="masked preview authority definition changed",
    ):
        _preview()


@pytest.mark.parametrize("forgery", ["not-json", 1, "{"])
def test_non_json_and_wrong_serializer_types_are_refused(monkeypatch, forgery):
    monkeypatch.setattr(
        redaction.json, "dumps", lambda *_args, **_kwargs: forgery,
    )
    with pytest.raises(
        redaction.OfflineRedactionRejected,
        match="masked preview authority definition changed",
    ):
        _preview()


def test_serializer_callback_cannot_shift_span_during_digest(monkeypatch):
    span = redaction.OfflineRedactionSpan(0, 20, "SECRET")
    source = "private fixture data"
    original = redaction.json.dumps

    def mutating(data, **kwargs):
        object.__setattr__(span, "label", "REPLACED")
        return original(data, **kwargs)

    monkeypatch.setattr(redaction.json, "dumps", mutating)
    with pytest.raises(
        redaction.OfflineRedactionRejected,
        match="masked preview authority definition changed",
    ):
        redaction.preview_offline_redaction(
            source, owner_digest="a" * 64, scope_digest="b" * 64,
            retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            spans=(span,),
        )
    assert span.label == "SECRET"
