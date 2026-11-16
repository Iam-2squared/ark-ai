"""Offline context index rejects over-budget private text before encoding.

All inputs here are synthetic and memory-only; results contain no document text
and cannot establish identity, consent, or disclosure authority.
"""

from __future__ import annotations

import dataclasses
import hashlib

import pytest

from ark import offline_text_index as index


_OWNER = "a" * 64
_SCOPE = "b" * 64
_DOC_ID = "doc_" + "c" * 16
_SMALL = "alpha"
_DIGEST = hashlib.sha256(_SMALL.encode()).hexdigest()


def _query() -> index.OfflineIndexQuery:
    document = index.OfflineIndexDocument(
        _DOC_ID, _OWNER, _SCOPE, _DIGEST, _SMALL,
    )
    return index.OfflineIndexQuery(
        _OWNER, _SCOPE, _DIGEST, _SMALL, (document,), (_DOC_ID,),
    )


@pytest.mark.parametrize(
    ("field", "text"),
    (
        ("query", "a" * 513),
        ("query", "a" * 200_000),
        ("query", "あ" * 513),
        ("document", "a" * 65_537),
        ("document", "a" * 200_000),
        ("document", "あ" * 65_537),
    ),
)
def test_oversized_text_rejected_as_budget_not_digest_mismatch(
    field: str, text: str,
) -> None:
    request = _query()
    if field == "query":
        request = dataclasses.replace(request, query=text)
    else:
        forged_doc = dataclasses.replace(request.documents[0], text=text)
        request = dataclasses.replace(request, documents=(forged_doc,))
    with pytest.raises(index.OfflineIndexRejected, match="local text budget exceeded"):
        index.search_offline_text(request)


def test_exact_ascii_query_codepoint_boundary_is_still_valid() -> None:
    encoded = index._encode_text("x" * 512, 512, empty_allowed=False)
    assert encoded == b"x" * 512


def test_utf8_byte_budget_is_not_weakened_by_codepoint_preflight() -> None:
    with pytest.raises(index.OfflineIndexRejected, match="local text budget exceeded"):
        index._encode_text("あ" * 171, 512, empty_allowed=False)


def test_normal_search_remains_deterministic_and_inert() -> None:
    result = index.search_offline_text(_query())
    assert result.scanned_count == 1
    assert result.hits[0].document_id == _DOC_ID
    assert result.identity_authenticated is False
    assert result.disclosure_authorized is False
    assert result.revocation_verified is False
