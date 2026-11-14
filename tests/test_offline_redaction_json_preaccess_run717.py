"""Redaction refuses replaced JSON callbacks before partial private fixture text.

Every fixture is synthetic, entirely local and never exported or sent to tools.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_redaction as redaction


@pytest.mark.parametrize("complete", [True, False])
@pytest.mark.parametrize("callback_name", ("dumps", "loads"))
def test_json_substitution_never_receives_private_masked_text(
    monkeypatch, complete, callback_name,
):
    source = "synthetic confidential note"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    spans = (
        redaction.OfflineRedactionSpan(
            0, len(source) if complete else 9, "PRIVATE",
        ),
    )
    calls = []

    def hostile(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("unreviewed JSON callback received private text")

    with monkeypatch.context() as patch:
        patch.setattr(redaction.json, callback_name, hostile)
        with pytest.raises(
            redaction.OfflineRedactionRejected,
            match="masked preview authority definition changed",
        ):
            redaction.preview_offline_redaction(
                source,
                owner_digest="a" * 64,
                scope_digest="b" * 64,
                retained_source_sha256=digest,
                spans=spans,
                require_complete=complete,
            )
    assert calls == []


def test_unmodified_json_preserves_masked_digest_and_denials():
    source = "synthetic confidential note"
    result = redaction.preview_offline_redaction(
        source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, len(source), "PRIVATE"),),
    )
    assert result.masked_text == "[MASK:PRIVATE]"
    assert result.consent_verified is False
    assert result.privacy_erasure_proven is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
