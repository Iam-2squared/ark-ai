"""Disconnected, metadata-only Memory snapshot delta review.

Inputs are untrusted synthetic claims. Matching fingerprints and tombstones
are not authoritative retention, deletion, provenance, consent or CAS proof.
No file, database, clock, network, or ToolBackend is accessed.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, fields

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ID = re.compile(r"mem_[0-9a-f]{16}\Z")
_TIME_LIMIT = 2**63 - 1
_MAX_ROWS = 64
_DOMAIN_SNAPSHOT = b"ARK-offline-memory-snapshot-delta-v1\0"
_DOMAIN_DELTA = b"ARK-offline-memory-claimed-delta-v1\0"


class OfflineMemoryDeltaRejected(ValueError):
    """A claimed snapshot transition lacks coherent, bounded metadata."""


@dataclass(frozen=True, slots=True)
class OfflineMemoryRowClaim:
    record_id: str
    scope_sha256: str
    content_sha256: str
    revision: int
    created_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class OfflineMemorySnapshotClaim:
    owner_sha256: str
    observed_at_ms: int
    rows: tuple[OfflineMemoryRowClaim, ...]


@dataclass(frozen=True, slots=True)
class OfflineMemoryRemovalClaim:
    record_id: str
    scope_sha256: str
    next_revision: int
    kind: str
    observed_at_ms: int
    event_sha256: str


@dataclass(frozen=True, slots=True)
class OfflineMemoryDeltaReview:
    prior_fingerprint: str
    current_fingerprint: str
    delta_fingerprint: str
    added_ids: tuple[str, ...] = field(repr=False)
    updated_ids: tuple[str, ...] = field(repr=False)
    removed_ids: tuple[str, ...] = field(repr=False)
    unchanged_count: int = 0

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def cross_store_atomicity_verified(self) -> bool:
        return False

    @property
    def deletion_or_erasure_proven(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False


_REVIEW_TYPE = OfflineMemoryDeltaReview


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _time(value: object) -> bool:
    return type(value) is int and 0 <= value <= _TIME_LIMIT


def _pin(item: object) -> tuple[object, tuple[object, ...]]:
    return item, tuple(getattr(item, field.name) for field in fields(item))


def _stable(pinned: tuple[object, tuple[object, ...]]) -> bool:
    obj, values = pinned
    return all(
        getattr(obj, f.name) is value
        for f, value in zip(fields(obj), values, strict=True)
    )


def _parse_snapshot(
    snapshot: OfflineMemorySnapshotClaim,
) -> tuple[tuple[tuple[object, ...], ...], str, tuple[object, ...]]:
    if type(snapshot) is not OfflineMemorySnapshotClaim:
        raise OfflineMemoryDeltaRejected("exact Memory snapshot type required")
    owner, now, rows = snapshot.owner_sha256, snapshot.observed_at_ms, snapshot.rows
    if (
        not _sha(owner) or not _time(now) or type(rows) is not tuple
        or len(rows) > _MAX_ROWS
        or any(type(row) is not OfflineMemoryRowClaim for row in rows)
    ):
        raise OfflineMemoryDeltaRejected("invalid bounded Memory snapshot")
    rows_pinned = tuple(_pin(row) for row in rows)
    values = tuple(fields for _, fields in rows_pinned)
    for record_id, scope, content, rev, created, expires in values:
        if (
            type(record_id) is not str or _ID.fullmatch(record_id) is None
            or not _sha(scope) or not _sha(content)
            or type(rev) is not int or not 1 <= rev <= _TIME_LIMIT
            or not _time(created) or not _time(expires)
            or not created <= now < expires
        ):
            raise OfflineMemoryDeltaRejected("unsafe, expired or malformed active row")
    ids = tuple(row[0] for row in values)
    if ids != tuple(sorted(set(ids))):
        raise OfflineMemoryDeltaRejected("Memory row IDs must be sorted and unique")
    payload = json.dumps(
        [owner, now, values], ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN_SNAPSHOT + payload).hexdigest()
    return values, digest, (snapshot, owner, now, rows, rows_pinned)


def fingerprint_offline_memory_snapshot(snapshot: OfflineMemorySnapshotClaim) -> str:
    """Fingerprint one bounded claim; this never authenticates its source."""
    _, digest, pinned = _parse_snapshot(snapshot)
    _check_snapshot_pinned(pinned)
    return digest


def _check_snapshot_pinned(pinned: tuple[object, ...]) -> None:
    snapshot, owner, observed, rows, row_pins = pinned
    if (
        snapshot.owner_sha256 is not owner
        or snapshot.observed_at_ms is not observed
        or snapshot.rows is not rows
        or len(rows) != len(row_pins)
        or any(actual is not pinned_row[0] or not _stable(pinned_row)
               for actual, pinned_row in zip(rows, row_pins, strict=True))
    ):
        raise OfflineMemoryDeltaRejected("Memory source carrier changed during review")


def review_offline_memory_delta(
    prior: OfflineMemorySnapshotClaim,
    current: OfflineMemorySnapshotClaim,
    *,
    retained_prior_fingerprint: str,
    retained_current_fingerprint: str,
    removals: tuple[OfflineMemoryRemovalClaim, ...] = (),
) -> OfflineMemoryDeltaReview:
    """Require revision continuity and explicit removal claims; NEVER replay.

    The caller must retain claimed fingerprint and receipt inputs elsewhere.
    This diagnostic cannot prove those records are independently authentic.
    """
    previous_rows, previous_hash, prior_pin = _parse_snapshot(prior)
    latest_rows, latest_hash, current_pin = _parse_snapshot(current)
    if (
        not _sha(retained_prior_fingerprint)
        or not _sha(retained_current_fingerprint)
        or previous_hash != retained_prior_fingerprint
        or latest_hash != retained_current_fingerprint
        or prior.owner_sha256 != current.owner_sha256
        or current.observed_at_ms < prior.observed_at_ms
        or type(removals) is not tuple or len(removals) > _MAX_ROWS
        or any(type(item) is not OfflineMemoryRemovalClaim for item in removals)
    ):
        raise OfflineMemoryDeltaRejected("Memory comparison basis invalid or unretained")
    removal_pins = tuple(_pin(row) for row in removals)
    removal_rows = tuple(values for _, values in removal_pins)
    removal_ids = tuple(row[0] for row in removal_rows)
    if any(type(item) is not str or _ID.fullmatch(item) is None for item in removal_ids):
        raise OfflineMemoryDeltaRejected("malformed removal record ID")
    if removal_ids != tuple(sorted(set(removal_ids))):
        raise OfflineMemoryDeltaRejected("duplicate or reordered removal receipt")
    before = {row[0]: row for row in previous_rows}
    after = {row[0]: row for row in latest_rows}
    dropped = tuple(sorted(before.keys() - after.keys()))
    if removal_ids != dropped:
        raise OfflineMemoryDeltaRejected("missing or orphaned removal receipt")
    for record_id, scope, revision, kind, when, event_hash in removal_rows:
        original = before[record_id]
        if (
            type(record_id) is not str or _ID.fullmatch(record_id) is None
            or scope != original[1] or type(scope) is not str
            or type(revision) is not int or not 1 <= revision <= _TIME_LIMIT
            or revision != original[3] + 1
            or type(kind) is not str or kind not in ("deleted", "expired")
            or not _time(when)
            or not prior.observed_at_ms <= when <= current.observed_at_ms
            or not _sha(event_hash)
            or (kind == "expired" and when < original[5])
        ):
            raise OfflineMemoryDeltaRejected("invalid or unsupported removal transition")
    added = tuple(sorted(after.keys() - before.keys()))
    updated: list[str] = []
    unchanged = 0
    for record_id, row in after.items():
        previous = before.get(record_id)
        if previous is None:
            if row[3] != 1:
                raise OfflineMemoryDeltaRejected("new Memory record has unknown history")
            continue
        if row[1] != previous[1] or row[4] != previous[4]:
            raise OfflineMemoryDeltaRejected("existing Memory identity or creation changed")
        if row[3] == previous[3]:
            if row != previous:
                raise OfflineMemoryDeltaRejected("Memory contents changed without CAS revision")
            unchanged += 1
        elif row[3] == previous[3] + 1:
            updated.append(record_id)
        else:
            raise OfflineMemoryDeltaRejected("Memory revision gap or rollback")
    _check_snapshot_pinned(prior_pin)
    _check_snapshot_pinned(current_pin)
    if any(not _stable(pin) for pin in removal_pins):
        raise OfflineMemoryDeltaRejected("removal receipt mutated during review")
    updated_ids = tuple(updated)
    decision = [previous_hash, latest_hash, added, updated_ids, dropped, removal_rows]
    payload = json.dumps(decision, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    digest = hashlib.sha256(_DOMAIN_DELTA + payload).hexdigest()
    _check_snapshot_pinned(prior_pin)
    _check_snapshot_pinned(current_pin)
    if any(not _stable(pin) for pin in removal_pins):
        raise OfflineMemoryDeltaRejected("removal receipt changed before result")
    result = OfflineMemoryDeltaReview(
        previous_hash, latest_hash, digest, added, updated_ids, dropped, unchanged,
    )
    # A synthetic checksum cannot upgrade Memory custody, deletion evidence,
    # or Tool authorization. Check exact result fields and denied authorities.
    if (
        type(result) is not _REVIEW_TYPE
        or result.prior_fingerprint is not previous_hash
        or result.current_fingerprint is not latest_hash
        or result.delta_fingerprint is not digest
        or result.added_ids is not added
        or result.updated_ids is not updated_ids
        or result.removed_ids is not dropped
        or type(result.unchanged_count) is not int
        or result.unchanged_count != unchanged
        or result.source_authenticated is not False
        or result.cross_store_atomicity_verified is not False
        or result.deletion_or_erasure_proven is not False
        or result.tool_dispatch_authorized is not False
    ):
        raise OfflineMemoryDeltaRejected(
            "constructed Memory delta changed or claims authority"
        )
    # False-returning authority getters can have side effects. Recheck the
    # inputs and result after those getters, without granting any permission.
    _check_snapshot_pinned(prior_pin)
    _check_snapshot_pinned(current_pin)
    if any(not _stable(pin) for pin in removal_pins):
        raise OfflineMemoryDeltaRejected("removal receipt changed during result review")
    if (
        type(result) is not _REVIEW_TYPE
        or result.prior_fingerprint is not previous_hash
        or result.current_fingerprint is not latest_hash
        or result.delta_fingerprint is not digest
        or result.added_ids is not added
        or result.updated_ids is not updated_ids
        or result.removed_ids is not dropped
        or type(result.unchanged_count) is not int
        or result.unchanged_count != unchanged
    ):
        raise OfflineMemoryDeltaRejected("Memory delta changed after authority review")
    return result
