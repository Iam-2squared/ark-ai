"""Disconnected lexical index tests; no private or persistent records."""

import dataclasses
import hashlib

import pytest

from ark.offline_text_index import (
    OfflineIndexDocument, OfflineIndexQuery, OfflineIndexRejected, search_offline_text,
)

SHA = "a" * 64
SCOPE = "b" * 64


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def doc(label, text, *, owner=SHA, scope=SCOPE):
    return OfflineIndexDocument("doc_" + label * 16, owner, scope, digest(text), text)


def query(text="alpha", documents=None, **kwargs):
    if documents is None:
        documents = (doc("1", "alpha beta"), doc("2", "alpha alpha gamma"))
    opts = dict(owner_sha256=SHA, scope_sha256=SCOPE, query_sha256=digest(text),
                query=text, documents=documents,
                expected_document_ids=tuple(sorted(x.document_id for x in documents)))
    opts.update(kwargs)
    return OfflineIndexQuery(**opts)


def test_ranking_and_determinism():
    request = query()
    one = search_offline_text(request)
    two = search_offline_text(request)
    assert one == two
    assert [h.document_id for h in one.hits] == ["doc_" + "2" * 16, "doc_" + "1" * 16]
    assert [h.score for h in one.hits] == [102, 101]
    assert one.scanned_count == 2
    assert one.query_token_count == 1
    assert len(one.inventory_sha256) == len(one.result_sha256) == 64
    assert not one.identity_authenticated
    assert not one.disclosure_authorized
    assert not one.revocation_verified
    assert "alpha" not in repr(one)


def test_unicode_and_casefold():
    q = query("ＫＡＮＡ 東京", (doc("1", "kana 東京"), doc("2", "KANA")))
    result = search_offline_text(q)
    assert [h.distinct_matches for h in result.hits] == [2, 1]


def test_tie_order_independent_of_corpus_order():
    docs = (doc("2", "alpha"), doc("1", "alpha"))
    result = search_offline_text(query(documents=docs))
    assert [h.document_id for h in result.hits] == ["doc_" + "1" * 16, "doc_" + "2" * 16]


def test_no_matches_still_scans_complete():
    out = search_offline_text(query("missing"))
    assert out.hits == () and out.scanned_count == 2


def test_empty_document_is_valid():
    out = search_offline_text(query(documents=(doc("1", ""),)))
    assert out.hits == ()


def test_max_eight_hits():
    docs = tuple(doc(format(i, "x"), "alpha") for i in range(9))
    out = search_offline_text(query(documents=docs))
    assert len(out.hits) == 8


def test_tf_capped_at_eight():
    docs = (doc("1", " ".join(["alpha"] * 100)),)
    assert search_offline_text(query(documents=docs)).hits[0].score == 108


@pytest.mark.parametrize("override", [
    {"owner_sha256": "A" * 64}, {"scope_sha256": "0"},
    {"query_sha256": "0" * 64}, {"query_sha256": 1},
    {"limit": 0}, {"limit": 9}, {"limit": True},
    {"query": ""}, {"query": "!!!"}, {"query": "x" * 513},
    {"query": "alpha " * 17}, {"query": "\ud800"},
    {"documents": []}, {"documents": ()},
    {"expected_document_ids": []},
    {"expected_document_ids": ("doc_" + "1" * 16,)},
    {"expected_document_ids": ("doc_" + "2" * 16, "doc_" + "1" * 16)},
])
def test_bad_query_rejected(override):
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(query(**override))


@pytest.mark.parametrize("bad", [
    doc("1", "secret", scope="f" * 64),
    doc("1", "secret", owner="f" * 64),
    dataclasses.replace(doc("1", "secret"), text_sha256="0" * 64),
    dataclasses.replace(doc("1", "secret"), document_id="../secret"),
    dataclasses.replace(doc("1", "secret"), text="\ud800"),
    dataclasses.replace(doc("1", "secret"), text="x" * 65_537),
    dataclasses.replace(doc("1", "secret"), text_sha256=True),
    dataclasses.replace(doc("1", "secret"), text=42),
])
def test_bad_doc_rejected(bad):
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(query(documents=(bad,)))


def test_duplicate_ids_rejected():
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(query(documents=(doc("1", "a"), doc("1", "b"))))


def test_total_byte_budget_rejected():
    docs = tuple(doc(format(i, "x"), "x" * 64_000) for i in range(3))
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(query(documents=docs))


def test_document_count_rejected():
    docs = tuple(doc(format(i, "x").zfill(16)[-1], "x") for i in range(33))
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(query(documents=docs))


def test_types_rejected():
    with pytest.raises(OfflineIndexRejected):
        search_offline_text({})
    with pytest.raises(OfflineIndexRejected):
        search_offline_text(dataclasses.replace(query(), documents=(object(),),
                                                     expected_document_ids=("doc_" + "1" * 16,)))


def test_original_carrier_swap_rejected(monkeypatch):
    import ark.offline_text_index as module

    request = query()
    orig = module._tokens

    def change(value):
        if value == "alpha":
            object.__setattr__(request, "query", "".join(["a", "l", "p", "h", "a"]))
        return orig(value)

    monkeypatch.setattr(module, "_tokens", change)
    with pytest.raises(OfflineIndexRejected, match="carriers"):
        search_offline_text(request)


def test_documents_not_returned():
    out = search_offline_text(query(documents=(doc("1", "verysecret alpha"),)))
    assert "verysecret" not in repr(out)
    assert all(not hasattr(hit, "text") for hit in out.hits)
