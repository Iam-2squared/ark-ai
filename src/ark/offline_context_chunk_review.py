"""Cross-check synthetic Context membership with private-free lexical chunk hits.

Only caller-provided, detached, bounded fixtures are used. Matching hashes
never authenticate consent, retained history, scope, time or source ownership.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import local_text_chunking as chunks
from . import offline_chunk_index_bridge as lexical
from . import offline_context_membership_guard as context

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-context-lexical-membership-v1\0"
_RECORD = context.ContextRecordClaim
_VETO = context.ContextScopeVetoClaim
_MEMBER = context.OfflineContextMembershipReview
_REVIEW_MEMBER = context.review_offline_context_membership
_BUNDLE = chunks.LocalTextChunkBundle
_INDEX = lexical.OfflineChunkIndexReview
_REVIEW_INDEX = lexical.search_detached_local_chunks
_MEMBER_FLAGS = (
    "consent_verified", "disclosure_authorized",
    "retention_authorized", "trusted_clock_verified",
)
_INDEX_FLAGS = (
    "consent_verified", "source_authenticated",
    "disclosure_authorized", "retention_authorized",
)
_ORIGINAL_MEMBER = tuple(vars(_MEMBER)[key] for key in _MEMBER_FLAGS)
_ORIGINAL_INDEX = tuple(vars(_INDEX)[key] for key in _INDEX_FLAGS)


class ContextLexicalRejected(ValueError):
    """Synthetic Context membership/index sources cannot be reconciled."""


@dataclass(frozen=True, slots=True)
class ContextLexicalReview:
    record_id: str
    membership_sha256: str
    index_evidence_sha256: str
    source_sha256: str
    hits: tuple[lexical.OfflineChunkIndexHit, ...]
    evidence_sha256: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def revocation_authenticated(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


_RESULT = ContextLexicalReview
_FLAGS = (
    "consent_verified", "disclosure_authorized",
    "revocation_authenticated", "trusted_clock_verified",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT)[key] for key in _FLAGS)


def review_context_chunk_index(
    records: tuple[context.ContextRecordClaim, ...],
    bundle: chunks.LocalTextChunkBundle,
    query: str,
    *,
    record_id: str,
    expected_record_ids: tuple[str, ...],
    allowed_scope_digests: tuple[str, ...],
    scope_vetoes: tuple[context.ContextScopeVetoClaim, ...],
    observed_at_ms: int,
    max_claim_age_ms: int,
    retained_membership_sha256: str,
    retained_bundle_sha256: str,
    query_sha256: str,
    limit: int = 8,
) -> ContextLexicalReview:
    """Reconcile all claimed Context rows and a single full text bundle.

    The result contains no original text and NEVER permits a private read,
    disclosure, replay, export, tool invocation, or scheduler side effect.
    """
    def authorities() -> None:
        if (
            context.ContextRecordClaim is not _RECORD
            or context.ContextScopeVetoClaim is not _VETO
            or context.OfflineContextMembershipReview is not _MEMBER
            or context.review_offline_context_membership is not _REVIEW_MEMBER
            or chunks.LocalTextChunkBundle is not _BUNDLE
            or lexical.OfflineChunkIndexReview is not _INDEX
            or lexical.search_detached_local_chunks is not _REVIEW_INDEX
            or ContextLexicalReview is not _RESULT
            or any(vars(_MEMBER).get(k) is not v for k, v in zip(
                _MEMBER_FLAGS, _ORIGINAL_MEMBER, strict=True,
            ))
            or any(vars(_INDEX).get(k) is not v for k, v in zip(
                _INDEX_FLAGS, _ORIGINAL_INDEX, strict=True,
            ))
            or any(vars(_RESULT).get(k) is not v for k, v in zip(
                _FLAGS, _ORIGINAL_RESULT, strict=True,
            ))
        ):
            raise ContextLexicalRejected("original Context/index authority changed")

    authorities()
    if (
        type(records) is not tuple or not 1 <= len(records) <= 32
        or any(type(row) is not _RECORD for row in records)
        or type(bundle) is not _BUNDLE
        or type(query) is not str
        or type(record_id) is not str
        or type(expected_record_ids) is not tuple
        or type(allowed_scope_digests) is not tuple
        or type(scope_vetoes) is not tuple
        or any(type(row) is not _VETO for row in scope_vetoes)
        or any(type(value) is not str or _SHA.fullmatch(value) is None for value in (
            retained_membership_sha256, retained_bundle_sha256, query_sha256,
        ))
    ):
        raise ContextLexicalRejected("exact bounded Context/index inputs required")

    record_epoch = tuple((
        row, row.record_id, row.owner_digest, row.scope_digest, row.content_sha256,
        row.captured_at_ms, row.expires_at_ms,
    ) for row in records)
    veto_epoch = tuple((
        row, row.scope_digest, row.revoked, row.observed_at_ms,
        row.continuity_sha256,
    ) for row in scope_vetoes)
    bundle_epoch = (
        bundle.owner_sha256, bundle.scope_sha256, bundle.source_sha256,
        bundle.chunk_byte_limit, bundle.chunks, bundle.bundle_sha256,
    )

    def epoch() -> None:
        authorities()
        if (
            any(type(row) is not _RECORD or row is not old
                or (row.record_id, row.owner_digest, row.scope_digest,
                    row.content_sha256, row.captured_at_ms, row.expires_at_ms) != tuple(fields)
                for row, (old, *fields) in zip(records, record_epoch, strict=True))
            or any(type(row) is not _VETO or row is not old
                or (row.scope_digest, row.revoked, row.observed_at_ms,
                    row.continuity_sha256) != tuple(fields)
                for row, (old, *fields) in zip(scope_vetoes, veto_epoch, strict=True))
            or (bundle.owner_sha256, bundle.scope_sha256, bundle.source_sha256,
                bundle.chunk_byte_limit, bundle.chunks, bundle.bundle_sha256) != bundle_epoch
        ):
            raise ContextLexicalRejected("Context/index source epoch changed")

    epoch()
    selected = tuple(row for row in records if row.record_id == record_id)
    if len(selected) != 1 or (
        selected[0].owner_digest != bundle.owner_sha256
        or selected[0].scope_digest != bundle.scope_sha256
        or selected[0].content_sha256 != bundle.source_sha256
    ):
        raise ContextLexicalRejected("selected Context record content mismatch")
    try:
        member = _REVIEW_MEMBER(
            records, expected_record_ids=expected_record_ids,
            owner_digest=bundle.owner_sha256,
            allowed_scope_digests=allowed_scope_digests,
            scope_vetoes=scope_vetoes, observed_at_ms=observed_at_ms,
            max_claim_age_ms=max_claim_age_ms,
        )
    except context.OfflineContextAdmissionRejected as exc:
        raise ContextLexicalRejected("Context membership rejected") from exc
    epoch()
    if (
        type(member) is not _MEMBER
        or member.membership_sha256 != retained_membership_sha256
        or member.owner_digest != bundle.owner_sha256
        or member.record_count != len(records)
        or member.scope_count != len(scope_vetoes)
    ):
        raise ContextLexicalRejected("retained Context membership mismatch")
    member_epoch = (
        member.owner_digest, member.record_count, member.scope_count,
        member.membership_sha256,
    )

    def check_member() -> None:
        epoch()
        if type(member) is not _MEMBER or (
            member.owner_digest, member.record_count, member.scope_count,
            member.membership_sha256,
        ) != member_epoch:
            raise ContextLexicalRejected("Context membership receipt changed")

    for flag in _MEMBER_FLAGS:
        if getattr(member, flag) is not False:
            raise ContextLexicalRejected("Context membership gained authority")
        check_member()
    try:
        indexed = _REVIEW_INDEX(
            bundle, query, query_sha256=query_sha256,
            retained_bundle_sha256=retained_bundle_sha256, limit=limit,
        )
    except lexical.OfflineChunkIndexRejected as exc:
        raise ContextLexicalRejected("detached chunk search rejected") from exc
    check_member()
    if (
        type(indexed) is not _INDEX or indexed.source_sha256 != bundle.source_sha256
        or indexed.scanned_count != len(bundle.chunks)
        or type(indexed.hits) is not tuple or len(indexed.hits) > 8
        or any(type(hit) is not lexical.OfflineChunkIndexHit for hit in indexed.hits)
    ):
        raise ContextLexicalRejected("index receipt invalid")
    index_epoch = (
        indexed.hits, indexed.scanned_count, indexed.source_sha256,
        indexed.index_inventory_sha256, indexed.evidence_sha256,
    )
    hit_epoch = tuple((
        hit, hit.chunk_index, hit.start, hit.end, hit.document_id, hit.score,
        hit.chunk_sha256,
    ) for hit in indexed.hits)

    def check_index() -> None:
        check_member()
        if (
            type(indexed) is not _INDEX
            or (indexed.hits, indexed.scanned_count, indexed.source_sha256,
                indexed.index_inventory_sha256, indexed.evidence_sha256) != index_epoch
            or len(indexed.hits) != len(hit_epoch)
            or any(type(hit) is not lexical.OfflineChunkIndexHit or hit is not old
                   or (hit.chunk_index, hit.start, hit.end, hit.document_id,
                       hit.score, hit.chunk_sha256) != tuple(fields)
                   for hit, (old, *fields) in zip(
                       indexed.hits, hit_epoch, strict=True,
                   ))
        ):
            raise ContextLexicalRejected("index evidence changed")

    for flag in _INDEX_FLAGS:
        if getattr(indexed, flag) is not False:
            raise ContextLexicalRejected("index gained authority")
        check_index()
    payload = json.dumps(
        (record_id, retained_membership_sha256, retained_bundle_sha256,
         query_sha256, indexed.evidence_sha256,
         [(hit.document_id, hit.chunk_sha256, hit.score) for hit in indexed.hits]),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    check_index()
    evidence = hashlib.sha256(_DOMAIN + payload).hexdigest()
    check_index()
    result = _RESULT(
        record_id, member.membership_sha256, indexed.evidence_sha256,
        bundle.source_sha256, indexed.hits, evidence,
    )
    result_epoch = (
        result.record_id, result.membership_sha256, result.index_evidence_sha256,
        result.source_sha256, result.hits, result.evidence_sha256,
    )
    for flag in _FLAGS:
        if getattr(result, flag) is not False:
            raise ContextLexicalRejected("Context chunk review gained authority")
        check_index()
        if type(result) is not _RESULT or (
            result.record_id, result.membership_sha256, result.index_evidence_sha256,
            result.source_sha256, result.hits, result.evidence_sha256,
        ) != result_epoch:
            raise ContextLexicalRejected("Context chunk review receipt changed")
    return result
