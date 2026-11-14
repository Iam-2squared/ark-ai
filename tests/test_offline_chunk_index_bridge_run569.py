"""Local-first exact chunks -> metadata-only lexical hit integration."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from ark import local_text_chunking as chunk
from ark import offline_chunk_index_bridge as bridge


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def bundle(text="apple banana pear apple", byte_limit=12, count=64):
    request = chunk.LocalChunkRequest(
        text, sha(text), "a" * 64, "b" * 64,
        chunk_byte_limit=byte_limit, chunk_limit=count,
    )
    return chunk.chunk_local_text(request)


def search(b=None, query="apple", *, query_digest=None, retained=None, limit=8):
    b = bundle() if b is None else b
    return bridge.search_detached_local_chunks(
        b, query,
        query_sha256=sha(query) if query_digest is None else query_digest,
        retained_bundle_sha256=b.bundle_sha256 if retained is None else retained,
        limit=limit,
    )


def test_hash_only_hits_from_verified_chunks_no_snippet_or_dispatch():
    b = bundle()
    r = search(b)
    assert r.scanned_count == len(b.chunks)
    assert r.source_sha256 == b.source_sha256
    assert len(r.hits) >= 1
    assert all(h.document_id.startswith("doc_") for h in r.hits)
    assert all(type(h.chunk_index) is int and h.start < h.end for h in r.hits)
    assert len(r.index_inventory_sha256) == len(r.evidence_sha256) == 64
    assert "apple" not in repr(r)
    assert r.consent_verified is False
    assert r.source_authenticated is False
    assert r.disclosure_authorized is False
    assert r.retention_authorized is False
    assert r == search(b)


def test_exact_chunk_range_and_retrieval_ranking_bound():
    b = bundle("red blue red", byte_limit=7)
    r = search(b, "red")
    assert r.hits
    assert len(r.hits) <= 8
    for hit in r.hits:
        piece = b.chunks[hit.chunk_index]
        assert (hit.start, hit.end, hit.chunk_sha256) == (
            piece.start, piece.end, piece.sha256,
        )


@pytest.mark.parametrize("bad", (0, -1, 9, True, 2.0, None))
def test_no_silent_hit_limit_bypass(bad):
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="bounded"):
        search(limit=bad)


def test_more_than_32_chunks_never_partially_indexed():
    b = bundle("a" * 33, byte_limit=1)
    assert len(b.chunks) == 33
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="bounded"):
        search(b, "a")


@pytest.mark.parametrize("bad", ("", "A" * 64, "x" * 63, None))
def test_retained_bundle_digest_must_match(bad):
    b = bundle()
    with pytest.raises(bridge.OfflineChunkIndexRejected):
        bridge.search_detached_local_chunks(
            b, "apple", query_sha256=sha("apple"),
            retained_bundle_sha256=bad,
        )


def test_query_sha_mismatch_denied():
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="digest mismatch"):
        search(query_digest="0" * 64)


@pytest.mark.parametrize("bad_query", ("", "\ud800"))
def test_empty_or_invalid_unicode_query_fails_closed(bad_query):
    b = bundle()
    with pytest.raises(bridge.OfflineChunkIndexRejected):
        bridge.search_detached_local_chunks(
            b, bad_query, query_sha256="0" * 64,
            retained_bundle_sha256=b.bundle_sha256,
        )


def test_forged_bundle_membership_denied():
    b = bundle()
    forged = replace(b, owner_sha256="c" * 64)
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="rejected"):
        search(forged)


@pytest.mark.parametrize("flag", bridge._RESULT_DENIAL_NAMES)
def test_result_original_false_only_authority_cannot_be_replaced(monkeypatch, flag):
    monkeypatch.setattr(bridge.OfflineChunkIndexReview, flag, property(lambda _: False))
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="authority changed"):
        search()


@pytest.mark.parametrize("flag", bridge._BUNDLE_DENIAL_NAMES)
def test_bundle_original_false_only_authority_cannot_be_replaced(monkeypatch, flag):
    monkeypatch.setattr(chunk.LocalTextChunkBundle, flag, property(lambda _: False))
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="authority changed"):
        search()


def test_retained_source_carriers_cannot_mutate_inside_sha_callback(monkeypatch):
    b = bundle()
    piece = b.chunks[0]
    real = bridge.hashlib.sha256
    changed = [False]

    def mutate(data):
        if not changed[0]:
            changed[0] = True
            object.__setattr__(piece, "text", "forged")
        return real(data)

    monkeypatch.setattr(bridge.hashlib, "sha256", mutate)
    with pytest.raises(
        bridge.OfflineChunkIndexRejected, match="source evidence changed",
    ):
        search(b, query_digest=real(b"apple").hexdigest())


@pytest.mark.parametrize("query", ("x" * 513, "🙂" * 129))
def test_query_codepoint_and_utf8_byte_caps_precede_hashing(query):
    with pytest.raises(bridge.OfflineChunkIndexRejected, match="bounded|byte budget"):
        search(query=query)
