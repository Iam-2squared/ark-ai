"""Offline lexical search must deny forged input accessors before execution.

Disconnected literal fixtures only; no filesystem, model, Memory or disclosure.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_text_index as index


def _query():
    content = "alpha beta"
    row = index.OfflineIndexDocument(
        "doc_" + "1" * 16, "a" * 64, "b" * 64,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), content,
    )
    return index.OfflineIndexQuery(
        "a" * 64, "b" * 64, hashlib.sha256(b"alpha").hexdigest(),
        "alpha", (row,), (row.document_id,),
    )


@pytest.mark.parametrize(
    "target,field",
    (
        ("query", "query"),
        ("query", "documents"),
        ("query", "expected_document_ids"),
        ("query", "__getattribute__"),
        ("document", "text"),
        ("document", "document_id"),
        ("document", "text_sha256"),
        ("document", "__getattr__"),
    ),
)
def test_preinstalled_input_slot_does_not_execute(
    monkeypatch, target, field,
):
    request = _query()
    cls = (
        index.OfflineIndexQuery if target == "query"
        else index.OfflineIndexDocument
    )
    invoked = []

    def hostile(*_args, **_kwargs):
        invoked.append("executed")
        raise AssertionError("forged lexical input getter executed")

    replacement = hostile if field.startswith("__") else property(hostile)
    with monkeypatch.context() as patch:
        patch.setattr(cls, field, replacement, raising=False)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)
    assert invoked == []


@pytest.mark.parametrize("target", ("query", "document"))
def test_tokenization_callback_cannot_install_late_input_getter(
    monkeypatch, target,
):
    request = _query()
    klass, field = (
        (index.OfflineIndexQuery, "documents")
        if target == "query"
        else (index.OfflineIndexDocument, "text")
    )
    invoked = []
    original = index._tokens

    def hostile(*_args, **_kwargs):
        invoked.append("executed")
        raise AssertionError("late lexical input getter executed")

    with monkeypatch.context() as patch:
        def changed(text):
            tokens = original(text)
            patch.setattr(klass, field, property(hostile))
            return tokens

        patch.setattr(index, "_tokens", changed)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)
    assert invoked == []


def test_clean_local_search_still_returns_only_scoped_hit_metadata():
    result = index.search_offline_text(_query())
    assert len(result.hits) == 1
    assert result.hits[0].distinct_matches == 1
    assert result.identity_authenticated is False
    assert result.disclosure_authorized is False
    assert result.revocation_verified is False
    assert "alpha beta" not in repr(result)
