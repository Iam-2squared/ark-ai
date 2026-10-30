"""Metadata-only, deny-only admission review for synthetic Context snapshots.

No personal text is read or emitted. All expected membership, scope veto,
clock, retention and content hashes are supplied by an untrusted caller.
Matching this review cannot establish consent, provenance, disclosure rights,
or a coherent cross-SQLite snapshot. Never use its result as an export grant.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_RECORD = re.compile(r"ctx_[0-9a-f]{16}\Z")
_DOMAIN = b"ARK-detached-context-membership-guard-v1\0"
_MAX_TIME = 2**63 - 1


class OfflineContextAdmissionRejected(ValueError):
    """The synthetic Context metadata is incomplete, stale or inconsistent."""


@dataclass(frozen=True, slots=True)
class ContextRecordClaim:
    record_id: str
    owner_digest: str
    scope_digest: str
    content_sha256: str
    captured_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class ContextScopeVetoClaim:
    scope_digest: str
    revoked: bool
    observed_at_ms: int
    continuity_sha256: str


@dataclass(frozen=True, slots=True)
class OfflineContextMembershipReview:
    owner_digest: str
    record_count: int
    scope_count: int
    membership_sha256: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def retention_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


_MEMBERSHIP_RESULT_TYPE = OfflineContextMembershipReview


def review_offline_context_membership(
    records: tuple[ContextRecordClaim, ...],
    *,
    expected_record_ids: tuple[str, ...],
    owner_digest: str,
    allowed_scope_digests: tuple[str, ...],
    scope_vetoes: tuple[ContextScopeVetoClaim, ...],
    observed_at_ms: int,
    max_claim_age_ms: int,
) -> OfflineContextMembershipReview:
    """Reject missing, foreign, revoked, stale, reordered or replaced metadata.

    The caller MUST obtain expected_record_ids and veto history from genuinely
    independent sources in any future trusted integration. This *standalone*
    review does not fetch or authenticate them and never releases content.
    """
    if (
        type(records) is not tuple or not 1 <= len(records) <= 32
        or any(type(row) is not ContextRecordClaim for row in records)
        or type(expected_record_ids) is not tuple
        or type(allowed_scope_digests) is not tuple
        or not 1 <= len(allowed_scope_digests) <= 16
        or type(scope_vetoes) is not tuple
        or len(scope_vetoes) != len(allowed_scope_digests)
        or any(type(row) is not ContextScopeVetoClaim for row in scope_vetoes)
        or type(owner_digest) is not str or _SHA.fullmatch(owner_digest) is None
        or type(observed_at_ms) is not int or not 0 <= observed_at_ms <= _MAX_TIME
        or type(max_claim_age_ms) is not int or not 0 <= max_claim_age_ms <= _MAX_TIME
    ):
        raise OfflineContextAdmissionRejected("invalid exact Context envelope")
    roots = (records, expected_record_ids, owner_digest, allowed_scope_digests,
             scope_vetoes, observed_at_ms, max_claim_age_ms)
    record_origins = tuple(records)
    veto_origins = tuple(scope_vetoes)
    record_fields = tuple((row.record_id, row.owner_digest, row.scope_digest,
                           row.content_sha256, row.captured_at_ms, row.expires_at_ms)
                          for row in records)
    veto_fields = tuple((row.scope_digest, row.revoked, row.observed_at_ms,
                         row.continuity_sha256) for row in scope_vetoes)

    def epoch() -> None:
        if (
            any(now is not before for now, before in zip(
                (records, expected_record_ids, owner_digest, allowed_scope_digests,
                 scope_vetoes, observed_at_ms, max_claim_age_ms), roots, strict=True,
            ))
            or any(row is not original or any(
                current is not pinned for current, pinned in zip(
                    (row.record_id, row.owner_digest, row.scope_digest,
                     row.content_sha256, row.captured_at_ms, row.expires_at_ms),
                    fields, strict=True,
                )
            ) for row, original, fields in zip(
                records, record_origins, record_fields, strict=True,
            ))
            or any(row is not original or any(
                current is not pinned for current, pinned in zip(
                    (row.scope_digest, row.revoked, row.observed_at_ms,
                     row.continuity_sha256), fields, strict=True,
                )
            ) for row, original, fields in zip(
                scope_vetoes, veto_origins, veto_fields, strict=True,
            ))
        ):
            raise OfflineContextAdmissionRejected("Context metadata carrier replaced")

    epoch()
    if (
        type(expected_record_ids) is not tuple
        or len(expected_record_ids) != len(records)
        or any(type(name) is not str or _RECORD.fullmatch(name) is None
               for name in expected_record_ids)
        or expected_record_ids != tuple(sorted(set(expected_record_ids)))
        or any(type(name) is not str or _SHA.fullmatch(name) is None
               for name in allowed_scope_digests)
        or allowed_scope_digests != tuple(sorted(set(allowed_scope_digests)))
    ):
        raise OfflineContextAdmissionRejected("invalid independently expected membership")
    for wanted, row in zip(expected_record_ids, record_fields, strict=True):
        epoch()
        record_id, owner, scope, content_sha, capture, expiry = row
        if (
            type(record_id) is not str or record_id != wanted
            or type(owner) is not str or owner != owner_digest
            or type(scope) is not str or scope not in allowed_scope_digests
            or type(content_sha) is not str or _SHA.fullmatch(content_sha) is None
            or type(capture) is not int or type(expiry) is not int
            or not 0 <= capture <= observed_at_ms < expiry <= _MAX_TIME
            or observed_at_ms - capture > max_claim_age_ms
        ):
            raise OfflineContextAdmissionRejected("unsafe, stale or foreign record")
        epoch()
    for expected_scope, (scope, revoked, sampled, continuity) in zip(
        allowed_scope_digests, veto_fields, strict=True,
    ):
        epoch()
        if (
            type(scope) is not str or scope != expected_scope
            or type(revoked) is not bool or revoked
            or type(sampled) is not int or not 0 <= sampled <= observed_at_ms
            or observed_at_ms - sampled > max_claim_age_ms
            or type(continuity) is not str or _SHA.fullmatch(continuity) is None
        ):
            raise OfflineContextAdmissionRejected("missing, stale or revoked scope veto")
        epoch()
    payload = json.dumps(
        {"owner": owner_digest, "expected": expected_record_ids,
         "records": record_fields, "scope_vetoes": veto_fields,
         "observed_at_ms": observed_at_ms, "max_claim_age_ms": max_claim_age_ms},
        sort_keys=True, ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    if len(payload) > 24_576:
        raise OfflineContextAdmissionRejected("Context metadata budget exceeded")
    epoch()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    epoch()
    result = OfflineContextMembershipReview(
        owner_digest, len(records), len(scope_vetoes), digest,
    )
    epoch()
    if (
        type(result) is not _MEMBERSHIP_RESULT_TYPE
        or result.owner_digest is not owner_digest
        or result.record_count != len(records)
        or result.scope_count != len(scope_vetoes)
        or result.membership_sha256 is not digest
    ):
        raise OfflineContextAdmissionRejected("constructed admission review mutated")
    return result
