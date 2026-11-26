"""Redaction never uses rebound grammar, budgets or domain for private data.

All content is synthetic, strictly local, and never exported or executed.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_redaction as redaction


class UntrustedMatcher:
    def __init__(self):
        self.calls = 0

    def fullmatch(self, _value):
        self.calls += 1
        raise AssertionError("unreviewed matcher received private labels")


@pytest.mark.parametrize("complete", [True, False])
@pytest.mark.parametrize(
    ("name", "alternative"),
    (
        ("_SHA", "matcher"),
        ("_LABEL", "matcher"),
        ("_DOMAIN", b"unreviewed-hash-domain"),
        ("_MAX_TEXT", 100_000_000),
        ("_MAX_TEXT", True),
        ("_MAX_SPANS", 100_000),
        ("_MAX_SPANS", False),
    ),
)
def test_rebound_redaction_protocol_refused_before_private_review(
    monkeypatch, complete, name, alternative,
):
    source = "synthetic protected text"
    retained = hashlib.sha256(source.encode()).hexdigest()
    spans = (
        redaction.OfflineRedactionSpan(
            0, len(source) if complete else 9, "PRIVATE",
        ),
    )
    matcher = UntrustedMatcher() if alternative == "matcher" else None
    replacement = matcher if matcher is not None else alternative
    with monkeypatch.context() as patch:
        patch.setattr(redaction, name, replacement)
        with pytest.raises(
            redaction.OfflineRedactionRejected,
            match="masked preview authority definition changed",
        ):
            redaction.preview_offline_redaction(
                source,
                owner_digest="a" * 64,
                scope_digest="b" * 64,
                retained_source_sha256=retained,
                spans=spans,
                require_complete=complete,
            )
    if matcher is not None:
        assert matcher.calls == 0


def test_original_full_mask_retains_no_plaintext_and_no_authority():
    source = "private synthetic text"
    result = redaction.preview_offline_redaction(
        source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, len(source), "PRIVATE"),),
    )
    assert result.masked_text == "[MASK:PRIVATE]"
    assert result.masked_characters == len(source)
    assert result.complete_masking is True
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.privacy_erasure_proven is False
