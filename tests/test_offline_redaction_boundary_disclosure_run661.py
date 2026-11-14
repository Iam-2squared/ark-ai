"""Exact Unicode codepoint masking boundaries never imply export consent.

All strings are invented fixture literals. No private store, remote endpoint,
automatic PII detector or external disclosure is exercised.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.offline_context_redaction import (
    OfflineRedactionRejected,
    OfflineRedactionSpan,
    preview_offline_redaction,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _preview(text, spans, *, complete=True):
    return preview_offline_redaction(
        text,
        owner_digest=_OWNER,
        scope_digest=_SCOPE,
        retained_source_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        spans=spans,
        require_complete=complete,
    )


@pytest.mark.parametrize("text", ("👩‍💻", "e\u0301", "日🚀漢", "A\u200dB"))
def test_adjacent_spans_cover_exact_codepoints_without_disclosure(text):
    assert len(text) >= 2
    view = _preview(
        text,
        (
            OfflineRedactionSpan(0, 1, "PRIVATE"),
            OfflineRedactionSpan(1, len(text), "PRIVATE"),
        ),
    )
    assert view.masked_text == "[MASK:PRIVATE][MASK:PRIVATE]"
    assert view.masked_characters == len(text)
    assert view.complete_masking is True
    assert view.consent_verified is False
    assert view.privacy_erasure_proven is False
    assert view.external_export_authorized is False
    assert view.tool_dispatch_authorized is False
    assert text not in repr(view)


@pytest.mark.parametrize("omission", ("interior_gap", "trailing_gap", "overlap"))
def test_incomplete_or_overlapping_boundaries_cannot_claim_full_mask(omission):
    text = "A秘密🚀Z"
    if omission == "interior_gap":
        spans = (
            OfflineRedactionSpan(0, 1, "PRIVATE"),
            OfflineRedactionSpan(2, len(text), "PRIVATE"),
        )
    elif omission == "trailing_gap":
        spans = (OfflineRedactionSpan(0, len(text) - 1, "PRIVATE"),)
    else:
        spans = (
            OfflineRedactionSpan(0, 3, "PRIVATE"),
            OfflineRedactionSpan(2, len(text), "PRIVATE"),
        )
    with pytest.raises(OfflineRedactionRejected):
        _preview(text, spans)


def test_partial_preview_may_expose_tail_but_still_cannot_authorize_export():
    text = "秘密🚀Z"
    view = _preview(
        text, (OfflineRedactionSpan(0, len(text) - 1, "PRIVATE"),),
        complete=False,
    )
    assert view.masked_text == "[MASK:PRIVATE]Z"
    assert view.complete_masking is False
    assert view.masked_characters == len(text) - 1
    assert view.external_export_authorized is False
    assert view.tool_dispatch_authorized is False
    assert view.consent_verified is False
