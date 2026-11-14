"""Standalone negative/positive redaction fixture regressions."""

import hashlib
from dataclasses import FrozenInstanceError

import pytest

from ark.offline_context_redaction import (
    OfflineRedactionRejected,
    OfflineRedactionSpan,
    RedactedOfflinePreview,
    preview_offline_redaction,
)

OWNER = "a" * 64
SCOPE = "b" * 64


def redact(text="Alice", spans=None, **kwargs):
    if spans is None:
        spans = (OfflineRedactionSpan(0, len(text), "PERSON"),)
    data = dict(
        owner_digest=OWNER, scope_digest=SCOPE,
        retained_source_sha256=hashlib.sha256(
            text.encode("utf-8", errors="surrogatepass")
        ).hexdigest(), spans=spans,
    )
    data.update(kwargs)
    return preview_offline_redaction(text, **data)


def test_full_mask_no_plaintext_and_no_authority():
    result = redact("Alice@example.com")
    assert type(result) is RedactedOfflinePreview
    assert result.masked_text == "[MASK:PERSON]"
    assert "Alice" not in repr(result)
    assert result.masked_characters == len("Alice@example.com")
    assert result.complete_masking
    assert not result.consent_verified
    assert not result.privacy_erasure_proven
    assert not result.external_export_authorized
    assert not result.tool_dispatch_authorized
    with pytest.raises(FrozenInstanceError):
        result.masked_text = "forged"


def test_split_full_mask_and_repeatable_digest():
    text = "Alice 1234"
    spans = (OfflineRedactionSpan(0, 6, "PERSON"), OfflineRedactionSpan(6, 10, "PIN"))
    result = redact(text, spans)
    assert result.masked_text == "[MASK:PERSON][MASK:PIN]"
    assert redact(text, spans) == result
    assert redact(text, spans, scope_digest="c" * 64).local_digest != result.local_digest
    assert redact(text, spans, owner_digest="c" * 64).local_digest != result.local_digest


def test_partial_requires_opt_in_and_is_never_export_authority():
    text = "Name Alice likes cake"
    spans = (OfflineRedactionSpan(5, 10, "PERSON"),)
    with pytest.raises(OfflineRedactionRejected):
        redact(text, spans)
    result = redact(text, spans, require_complete=False)
    assert result.masked_text == "Name [MASK:PERSON] likes cake"
    assert not result.complete_masking
    assert not result.external_export_authorized


@pytest.mark.parametrize("spans", [
    (),
    (OfflineRedactionSpan(1, 5, "PERSON"),),
    (OfflineRedactionSpan(0, 4, "PERSON"),),
    (OfflineRedactionSpan(0, 6, "PERSON"),),
    (OfflineRedactionSpan(0, 0, "PERSON"),),
    (OfflineRedactionSpan(True, 2, "PERSON"),),
    (OfflineRedactionSpan(0, False, "PERSON"),),
    (OfflineRedactionSpan(0, 5, "person"),),
    (OfflineRedactionSpan(0, 5, "PERSON/OTHER"),),
    (OfflineRedactionSpan(0, 5, "X" * 21),),
    (OfflineRedactionSpan(0, 5, "PERSON"), OfflineRedactionSpan(4, 5, "OTHER")),
    (OfflineRedactionSpan(0, 4, "PERSON"), OfflineRedactionSpan(4, 5, "OTHER"),
     OfflineRedactionSpan(5, 5, "PIN")),
])
def test_invalid_or_incomplete_coverage_denied(spans):
    with pytest.raises(OfflineRedactionRejected):
        redact(spans=spans)


@pytest.mark.parametrize("bad", [
    {"owner_digest": "bad"},
    {"scope_digest": "c" * 63},
    {"retained_source_sha256": "0" * 64},
    {"require_complete": 1},
    {"spans": [OfflineRedactionSpan(0, 5, "PERSON")]},
    {"spans": (OfflineRedactionSpan(0, 5, "PERSON"),) * 65},
])
def test_bad_input_rejected(bad):
    with pytest.raises(OfflineRedactionRejected):
        redact(**bad)


def test_invalid_surrogate_denied():
    with pytest.raises(OfflineRedactionRejected):
        redact("\ud800")


def test_large_content_denied():
    with pytest.raises(OfflineRedactionRejected):
        redact("a" * 8193)
    with pytest.raises(OfflineRedactionRejected):
        redact("日" * 3000)


def test_multibyte_indices_are_codepoints_not_bytes():
    spans = (OfflineRedactionSpan(0, 1, "JAPANESE"),
             OfflineRedactionSpan(1, 3, "NUMBER"))
    result = redact("日12", spans)
    assert result.masked_text == "[MASK:JAPANESE][MASK:NUMBER]"
    assert result.masked_characters == 3


def test_span_mutated_inside_digest_hash_denied(monkeypatch):
    span = OfflineRedactionSpan(0, 5, "PERSON")
    original_hash = hashlib.sha256
    def mutated_hash(payload=b""):
        object.__setattr__(span, "label", span.label.encode().decode())
        return original_hash(payload)
    monkeypatch.setattr("ark.offline_context_redaction.hashlib.sha256", mutated_hash)
    with pytest.raises(OfflineRedactionRejected):
        redact(spans=(span,))


def test_exact_span_types_and_empty_source_rejected():
    class FakeSpan(OfflineRedactionSpan):
        pass
    with pytest.raises(OfflineRedactionRejected):
        redact(spans=(FakeSpan(0, 5, "PERSON"),))
    with pytest.raises(OfflineRedactionRejected):
        redact("")


def test_full_mask_is_not_irreversible_erasure():
    result = redact("synthetic secret")
    assert result.source_sha256 == hashlib.sha256(b"synthetic secret").hexdigest()
    assert not result.privacy_erasure_proven
    assert result.masked_text != "synthetic secret"
