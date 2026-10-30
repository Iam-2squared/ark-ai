"""Local masking must not authorize privacy erasure, export or Tool effects."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

import ark.offline_context_redaction as mod

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _mask(text="local-fixture"):
    return mod.preview_offline_redaction(
        text,
        owner_digest=_OWNER,
        scope_digest=_SCOPE,
        retained_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        spans=(mod.OfflineRedactionSpan(0, len(text), "SECRET"),),
    )


def test_complete_mask_is_still_not_an_authorization():
    result = _mask("synthetic user detail")
    assert result.masked_text == "[MASK:SECRET]"
    assert result.complete_masking is True
    assert result.consent_verified is False
    assert result.privacy_erasure_proven is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert "synthetic user detail" not in repr(result)


@pytest.mark.parametrize("authority", (
    "consent_verified",
    "privacy_erasure_proven",
    "external_export_authorized",
    "tool_dispatch_authorized",
))
def test_forged_exact_type_redaction_authority_is_refused(monkeypatch, authority):
    monkeypatch.setattr(
        mod.RedactedOfflinePreview,
        authority,
        property(lambda _self: True),
    )
    with pytest.raises(mod.OfflineRedactionRejected, match="construction"):
        _mask()


def test_boolean_masked_character_count_is_not_an_integer_receipt(monkeypatch):
    original = mod.RedactedOfflinePreview

    def forged(*fields):
        return replace(original(*fields), masked_characters=True)

    monkeypatch.setattr(mod, "RedactedOfflinePreview", forged)
    with pytest.raises(mod.OfflineRedactionRejected, match="construction"):
        _mask("x")


def test_constructor_returning_unexpected_result_is_refused(monkeypatch):
    monkeypatch.setattr(mod, "RedactedOfflinePreview", lambda *_args: object())
    with pytest.raises(mod.OfflineRedactionRejected, match="construction"):
        _mask()


def test_full_mask_with_multiple_spans_retains_no_export_authority():
    text = "first second"
    result = mod.preview_offline_redaction(
        text,
        owner_digest=_OWNER,
        scope_digest=_SCOPE,
        retained_source_sha256=hashlib.sha256(text.encode()).hexdigest(),
        spans=(
            mod.OfflineRedactionSpan(0, 6, "FIRST"),
            mod.OfflineRedactionSpan(6, len(text), "SECOND"),
        ),
    )
    assert result.masked_text == "[MASK:FIRST][MASK:SECOND]"
    assert result.masked_characters == len(text)
    assert result.external_export_authorized is False
