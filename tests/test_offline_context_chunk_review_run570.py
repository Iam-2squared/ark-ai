"""Synthetic, disconnected Context membership to no-text chunk search."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from ark import local_text_chunking as chunks
from ark import offline_chunk_index_bridge as lexical
from ark import offline_context_chunk_review as joined
from ark import offline_context_membership_guard as context


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inputs(text="apple pear apple"):
    owner, scope = "a" * 64, "b" * 64
    bundle = chunks.chunk_local_text(chunks.LocalChunkRequest(
        text, sha(text), owner, scope, chunk_byte_limit=12,
    ))
    record = context.ContextRecordClaim(
        "ctx_" + "1" * 16, owner, scope, sha(text), 80, 200,
    )
    veto = context.ContextScopeVetoClaim(scope, False, 99, "c" * 64)
    records, vetoes = (record,), (veto,)
    membership = context.review_offline_context_membership(
        records, expected_record_ids=(record.record_id,), owner_digest=owner,
        allowed_scope_digests=(scope,), scope_vetoes=vetoes,
        observed_at_ms=100, max_claim_age_ms=30,
    )
    options = dict(
        record_id=record.record_id, expected_record_ids=(record.record_id,),
        allowed_scope_digests=(scope,), scope_vetoes=vetoes,
        observed_at_ms=100, max_claim_age_ms=30,
        retained_membership_sha256=membership.membership_sha256,
        retained_bundle_sha256=bundle.bundle_sha256,
        query_sha256=sha("apple"),
    )
    return records, bundle, options


def test_context_chunk_review_binds_only_positional_hits_and_hashes():
    records, bundle, options = inputs()
    r = joined.review_context_chunk_index(records, bundle, "apple", **options)
    assert r.record_id == records[0].record_id
    assert r.source_sha256 == bundle.source_sha256
    assert r.membership_sha256 == options["retained_membership_sha256"]
    assert r.hits and all(type(hit) is lexical.OfflineChunkIndexHit for hit in r.hits)
    assert "apple" not in repr(r)
    assert len(r.evidence_sha256) == len(r.index_evidence_sha256) == 64
    assert all(getattr(r, k) is False for k in joined._FLAGS)
    assert r == joined.review_context_chunk_index(records, bundle, "apple", **options)


@pytest.mark.parametrize("field,value", [
    ("record_id", "ctx_" + "2" * 16),
    ("owner_digest", "f" * 64),
    ("scope_digest", "f" * 64),
    ("content_sha256", "f" * 64),
    ("captured_at_ms", 0),
    ("expires_at_ms", 100),
])
def test_wrong_stale_foreign_or_unmatched_record_never_indexed(field, value):
    records, bundle, options = inputs()
    broken = (replace(records[0], **{field: value}),)
    with pytest.raises(joined.ContextLexicalRejected):
        joined.review_context_chunk_index(broken, bundle, "apple", **options)


@pytest.mark.parametrize("field,value", [
    ("revoked", True), ("observed_at_ms", 0),
    ("scope_digest", "f" * 64), ("continuity_sha256", "bad"),
])
def test_revoked_missing_or_stale_scope_claim_refused(field, value):
    records, bundle, options = inputs()
    veto = replace(options["scope_vetoes"][0], **{field: value})
    with pytest.raises(joined.ContextLexicalRejected):
        joined.review_context_chunk_index(
            records, bundle, "apple", **{**options, "scope_vetoes": (veto,)},
        )


@pytest.mark.parametrize("field,value", [
    ("retained_membership_sha256", "0" * 64),
    ("retained_bundle_sha256", "0" * 64),
    ("query_sha256", "0" * 64),
    ("allowed_scope_digests", ("f" * 64,)),
    ("observed_at_ms", 201),
    ("limit", 0),
    ("limit", True),
])
def test_digests_membership_time_and_budgets_do_not_silently_fallback(field, value):
    records, bundle, options = inputs()
    with pytest.raises(joined.ContextLexicalRejected):
        joined.review_context_chunk_index(
            records, bundle, "apple", **{**options, field: value},
        )


@pytest.mark.parametrize("flag", joined._FLAGS)
def test_context_join_original_false_only_authority_is_import_pinned(monkeypatch, flag):
    records, bundle, options = inputs()
    monkeypatch.setattr(joined.ContextLexicalReview, flag, property(lambda _: False))
    with pytest.raises(joined.ContextLexicalRejected, match="authority changed"):
        joined.review_context_chunk_index(records, bundle, "apple", **options)


def test_mutated_record_during_join_receipt_digestion_is_rejected(monkeypatch):
    records, bundle, options = inputs()
    original = joined.hashlib.sha256
    changed = [False]

    def mutate(data):
        if not changed[0] and data.startswith(joined._DOMAIN):
            changed[0] = True
            object.__setattr__(records[0], "expires_at_ms", 99)
        return original(data)

    monkeypatch.setattr(joined.hashlib, "sha256", mutate)
    with pytest.raises(joined.ContextLexicalRejected, match="epoch changed"):
        joined.review_context_chunk_index(records, bundle, "apple", **options)
    assert changed[0]
