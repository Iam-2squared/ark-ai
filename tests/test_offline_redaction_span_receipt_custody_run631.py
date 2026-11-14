"""Disconnected redaction rejects executable span and receipt class mutations.

The source is a synthetic fixture. A complete mask does not prove consent,
erasure, trusted provenance, external export or tool execution permission.
"""

import hashlib

import pytest

import ark.offline_context_redaction as redact


def _request():
    source = "synthetic local secret"
    return dict(
        text=source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(redact.OfflineRedactionSpan(0, len(source), "SECRET"),),
    )


class ExecutableField:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("executed")
        raise AssertionError("forged field descriptor must not run")


@pytest.mark.parametrize("field", redact._SPAN_FIELDS)
def test_span_field_descriptor_denied_before_source_hash(
    monkeypatch, field,
):
    request = _request()
    calls = []

    def forbidden_hash(*args, **kwargs):
        raise AssertionError("source must not be hashed with forged span field")

    with monkeypatch.context() as patch:
        patch.setattr(redact.OfflineRedactionSpan, field, ExecutableField(calls))
        patch.setattr(redact.hashlib, "sha256", forbidden_hash)
        with pytest.raises(redact.OfflineRedactionRejected,
                           match="authority definition changed"):
            redact.preview_offline_redaction(**request)
    assert calls == []


@pytest.mark.parametrize("field", redact._RESULT_FIELDS)
def test_receipt_field_descriptor_denied_before_source_hash(
    monkeypatch, field,
):
    request = _request()
    calls = []

    def forbidden_hash(*args, **kwargs):
        raise AssertionError("source must not be hashed with forged receipt field")

    with monkeypatch.context() as patch:
        patch.setattr(redact.RedactedOfflinePreview, field, ExecutableField(calls))
        patch.setattr(redact.hashlib, "sha256", forbidden_hash)
        with pytest.raises(redact.OfflineRedactionRejected,
                           match="authority definition changed"):
            redact.preview_offline_redaction(**request)
    assert calls == []


@pytest.mark.parametrize("name", ("__init__", "__getattribute__", "__getattr__"))
def test_receipt_hook_substitution_rejected_without_execution(
    monkeypatch, name,
):
    request = _request()
    calls = []

    def forbidden(*args, **kwargs):
        calls.append("executed")
        raise AssertionError("forged receipt hook must not run")

    with monkeypatch.context() as patch:
        patch.setattr(redact.RedactedOfflinePreview, name, forbidden,
                      raising=False)
        with pytest.raises(redact.OfflineRedactionRejected,
                           match="authority definition changed"):
            redact.preview_offline_redaction(**request)
    assert calls == []


def test_hash_callback_cannot_install_late_result_field(monkeypatch):
    request = _request()
    original_hash = redact.hashlib.sha256
    calls = []

    with monkeypatch.context() as patch:
        def changed_hash(payload=b""):
            patch.setattr(
                redact.RedactedOfflinePreview, "masked_text",
                ExecutableField(calls),
            )
            return original_hash(payload)

        patch.setattr(redact.hashlib, "sha256", changed_hash)
        with pytest.raises(redact.OfflineRedactionRejected,
                           match="authority definition changed"):
            redact.preview_offline_redaction(**request)
    assert calls == []


def test_original_complete_mask_remains_private_and_without_authority():
    request = _request()
    result = redact.preview_offline_redaction(**request)
    assert result.masked_text == "[MASK:SECRET]"
    assert request["text"] not in repr(result)
    assert result.complete_masking is True
    assert result.consent_verified is False
    assert result.privacy_erasure_proven is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
