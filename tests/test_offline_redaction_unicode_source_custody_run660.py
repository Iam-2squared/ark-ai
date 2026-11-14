"""Offline redaction binds exact Unicode source bytes, not visual equivalence.

This fixture never exports content or authenticates consent. The Unicode
normalization distinction is intentionally NOT a PII-detection feature.
"""

from __future__ import annotations

import hashlib
import unicodedata

import pytest

from ark.offline_context_redaction import (
    OfflineRedactionRejected,
    OfflineRedactionSpan,
    preview_offline_redaction,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _mask(text: str, source_hash: str):
    return preview_offline_redaction(
        text,
        owner_digest=_OWNER,
        scope_digest=_SCOPE,
        retained_source_sha256=source_hash,
        spans=(OfflineRedactionSpan(0, len(text), "PRIVATE"),),
    )


@pytest.mark.parametrize(
    ("source", "same_visible_text"),
    (
        ("é", "e\u0301"),
        ("Å", "A\u030a"),
        ("\u212b", "\u00c5"),
    ),
)
def test_normalization_equivalence_never_substitutes_source_custody(
    source, same_visible_text,
):
    assert source != same_visible_text
    assert unicodedata.normalize("NFC", source) == unicodedata.normalize(
        "NFC", same_visible_text,
    )
    old = hashlib.sha256(source.encode("utf-8")).hexdigest()
    new = hashlib.sha256(same_visible_text.encode("utf-8")).hexdigest()
    assert old != new

    first = _mask(source, old)
    second = _mask(same_visible_text, new)
    assert first.masked_text == second.masked_text == "[MASK:PRIVATE]"
    assert first.source_sha256 != second.source_sha256
    assert first.local_digest != second.local_digest
    assert first.complete_masking and second.complete_masking
    assert first.external_export_authorized is False
    assert second.privacy_erasure_proven is False
    with pytest.raises(OfflineRedactionRejected, match="independently retained"):
        _mask(same_visible_text, old)


def test_full_mask_covers_joiners_rtl_and_non_bmp_without_plaintext(tmp_path):
    del tmp_path  # This fixture performs no filesystem I/O.
    source = "👩‍👩‍👧‍👧 שלום \u200f confidentiality"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    receipt = _mask(source, digest)
    assert receipt.masked_text == "[MASK:PRIVATE]"
    assert receipt.masked_characters == len(source)
    assert receipt.source_sha256 == digest
    assert source not in repr(receipt)
    assert receipt.consent_verified is False
    assert receipt.privacy_erasure_proven is False
    assert receipt.external_export_authorized is False
    assert receipt.tool_dispatch_authorized is False
