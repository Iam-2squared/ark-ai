"""Offline index exact identifier widths before untrusted regex matching."""

from __future__ import annotations

import hashlib

import pytest

from ark.offline_text_index import (
    OfflineIndexDocument,
    OfflineIndexQuery,
    OfflineIndexRejected,
    search_offline_text,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64
_TEXT = "alpha"
_DOC_ID = "doc_" + "c" * 16


def _query(**overrides: object) -> OfflineIndexQuery:
    document = OfflineIndexDocument(
        _DOC_ID, _OWNER, _SCOPE, hashlib.sha256(_TEXT.encode()).hexdigest(), _TEXT,
    )
    args = {
        "owner_sha256": _OWNER,
        "scope_sha256": _SCOPE,
        "query_sha256": hashlib.sha256(_TEXT.encode()).hexdigest(),
        "query": _TEXT,
        "documents": (document,),
        "expected_document_ids": (_DOC_ID,),
    }
    args.update(overrides)
    return OfflineIndexQuery(**args)


@pytest.mark.parametrize("field", ("owner_sha256", "scope_sha256", "query_sha256"))
@pytest.mark.parametrize("size", (63, 65, 65_536))
def test_query_digest_width_denied_before_corpus_scan(field: str, size: int) -> None:
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(_query(**{field: "a" * size}))


@pytest.mark.parametrize("field", ("document_id", "text_sha256"))
@pytest.mark.parametrize("size", (63, 65, 65_536))
def test_document_identity_and_digest_width_denied(field: str, size: int) -> None:
    doc = _query().documents[0]
    payload = {
        "document_id": doc.document_id,
        "owner_sha256": doc.owner_sha256,
        "scope_sha256": doc.scope_sha256,
        "text_sha256": doc.text_sha256,
        "text": doc.text,
    }
    payload[field] = "a" * size
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(_query(documents=(OfflineIndexDocument(**payload),)))


@pytest.mark.parametrize("size", (19, 21, 65_536))
def test_expected_membership_id_width_denied(size: int) -> None:
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(_query(expected_document_ids=("a" * size,)))


def test_valid_complete_fixture_unchanged_and_never_disclosure_authority() -> None:
    result = search_offline_text(_query())
    assert result.scanned_count == 1
    assert result.hits[0].document_id == _DOC_ID
    assert result.disclosure_authorized is False
    assert result.identity_authenticated is False
    assert result.revocation_verified is False
