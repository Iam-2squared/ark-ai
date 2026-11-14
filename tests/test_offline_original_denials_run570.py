"""Original deny-only property integrity in disconnected text/Context review."""

from __future__ import annotations

import hashlib

import pytest

from ark import offline_context_membership_guard as context
from ark import offline_text_index as index


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def context_args():
    owner, scope = "a" * 64, "b" * 64
    claim = context.ContextRecordClaim(
        "ctx_" + "0" * 16, owner, scope, sha("content"), 10, 200,
    )
    veto = context.ContextScopeVetoClaim(scope, False, 99, "c" * 64)
    return ((claim,), dict(
        expected_record_ids=(claim.record_id,), owner_digest=owner,
        allowed_scope_digests=(scope,), scope_vetoes=(veto,),
        observed_at_ms=100, max_claim_age_ms=100,
    ))


def lexical_query():
    owner, scope, text, query = "a" * 64, "b" * 64, "alpha beta", "alpha"
    doc = index.OfflineIndexDocument(
        "doc_" + "1" * 16, owner, scope, sha(text), text,
    )
    return index.OfflineIndexQuery(
        owner, scope, sha(query), query, (doc,), (doc.document_id,),
    )


def test_context_authentic_denials_stay_inert():
    records, kwargs = context_args()
    result = context.review_offline_context_membership(records, **kwargs)
    assert result.record_count == 1
    assert all(getattr(result, flag) is False for flag in context._DENIAL_NAMES)


def test_index_authentic_denials_stay_inert():
    result = index.search_offline_text(lexical_query())
    assert result.scanned_count == 1
    assert len(result.hits) == 1
    assert all(getattr(result, flag) is False for flag in index._DENIAL_NAMES)


@pytest.mark.parametrize("flag", context._DENIAL_NAMES)
def test_context_false_spoof_refused_before_metadata(monkeypatch, flag):
    records, kwargs = context_args()
    monkeypatch.setattr(
        context.OfflineContextMembershipReview, flag, property(lambda _: False),
    )
    with pytest.raises(
        context.OfflineContextAdmissionRejected, match="original Context authority",
    ):
        context.review_offline_context_membership(records, **kwargs)


@pytest.mark.parametrize("flag", index._DENIAL_NAMES)
def test_lexical_false_spoof_refused_before_private_text(monkeypatch, flag):
    request = lexical_query()
    monkeypatch.setattr(
        index.OfflineIndexResult, flag, property(lambda _: False),
    )
    with pytest.raises(
        index.OfflineIndexRejected, match="original index authority",
    ):
        index.search_offline_text(request)


def test_context_false_spoof_during_hash_callback_refused(monkeypatch):
    records, kwargs = context_args()
    original = context.hashlib.sha256
    changed = [False]

    def swap(data):
        if not changed[0] and data.startswith(context._DOMAIN):
            changed[0] = True
            monkeypatch.setattr(
                context.OfflineContextMembershipReview,
                "consent_verified", property(lambda _: False),
            )
        return original(data)

    monkeypatch.setattr(context.hashlib, "sha256", swap)
    with pytest.raises(
        context.OfflineContextAdmissionRejected, match="original Context authority",
    ):
        context.review_offline_context_membership(records, **kwargs)
    assert changed[0]


def test_index_false_spoof_during_hash_callback_refused(monkeypatch):
    request = lexical_query()
    original = index.hashlib.sha256
    changed = [False]

    def swap(data):
        if not changed[0] and data.startswith(index._DOMAIN):
            changed[0] = True
            monkeypatch.setattr(
                index.OfflineIndexResult,
                "revocation_verified", property(lambda _: False),
            )
        return original(data)

    monkeypatch.setattr(index.hashlib, "sha256", swap)
    with pytest.raises(
        index.OfflineIndexRejected, match="original index authority",
    ):
        index.search_offline_text(request)
    assert changed[0]
