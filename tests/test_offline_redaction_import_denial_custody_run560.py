"""Import-pinned masking denial before any private synthetic source inspection.

A malicious always-False property is still code, not a trusted absence of
consent/export/erasure. Fixtures remain wholly local and non-authorizing.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_redaction as mod


def _request():
    source = "private synthetic fixture"
    return dict(
        text=source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(mod.OfflineRedactionSpan(0, len(source), "SECRET"),),
    )


@pytest.mark.parametrize("flag", mod._DENIAL_NAMES)
def test_installed_false_getter_is_rejected_before_private_hash(
    monkeypatch, flag,
):
    values = _request()
    called = []

    def malicious_getter(_result):
        called.append(flag)
        return False

    def forbidden_hash(*_args, **_kwargs):
        raise AssertionError("private source was hashed before authority preflight")

    monkeypatch.setattr(
        mod.RedactedOfflinePreview, flag, property(malicious_getter),
    )
    monkeypatch.setattr(mod.hashlib, "sha256", forbidden_hash)

    with pytest.raises(mod.OfflineRedactionRejected, match="authority definition changed"):
        mod.preview_offline_redaction(**values)
    assert called == []


def test_digest_callback_cannot_rebaseline_false_getter(monkeypatch):
    values = _request()
    original_hash = mod.hashlib.sha256

    def mutate_hash(payload=b""):
        monkeypatch.setattr(
            mod.RedactedOfflinePreview, "consent_verified",
            property(lambda _result: False),
        )
        return original_hash(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", mutate_hash)
    with pytest.raises(mod.OfflineRedactionRejected, match="authority definition changed"):
        mod.preview_offline_redaction(**values)


def test_original_denials_allow_complete_local_mask():
    result = mod.preview_offline_redaction(**_request())
    assert result.masked_text == "[MASK:SECRET]"
    assert result.complete_masking is True
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
