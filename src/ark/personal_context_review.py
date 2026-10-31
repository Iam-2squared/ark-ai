"""Ephemeral, disconnected Personal Context assembly over one Memory snapshot.

Receives only a prevalidated coherent local Memory snapshot; no external
fetches, durable plaintext copies, tools or permissions are created.
A content-free SHA witness is not independent provenance attestation.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .memory.coherent_snapshot_review import CoherentSnapshotReview
from .memory.contracts import MemoryRecord, MemoryScope
from .memory.sqlite_store import deterministic_memory_id

_MAX_INT = 2**63 - 1
_HEX = re.compile(r"[0-9a-f]{64}\Z")


class PersonalContextReviewRejected(RuntimeError):
    """A proposed context projection violates snapshot privacy/integrity."""


@dataclass(frozen=True, slots=True)
class ContextSelectionPolicy:
    total_limit: int
    per_namespace_limit: int
    policy_revision: str = "round_robin_v1"

    def __post_init__(self) -> None:
        if (
            type(self.total_limit) is not int
            or not 1 <= self.total_limit <= 100
            or type(self.per_namespace_limit) is not int
            or not 1 <= self.per_namespace_limit <= 100
            or type(self.policy_revision) is not str
            or not 1 <= len(self.policy_revision) <= 128
            or not self.policy_revision.strip()
        ):
            raise ValueError("invalid exact Personal Context budget/policy")


@dataclass(frozen=True, slots=True)
class SyntheticContextItem:
    memory_id: str
    namespace: str
    content: str
    revision: int
    provenance_id: str


@dataclass(frozen=True, slots=True)
class SyntheticContextBundle:
    items: tuple[SyntheticContextItem, ...]
    bundle_id: str
    snapshot_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


# A replaced fixture constructor must not substitute an altered context bundle.
_BUNDLE_RESULT_TYPE = SyntheticContextBundle


def _hash(label: str, payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(label.encode("utf-8") + b"\0" + encoded).hexdigest()


def review_personal_context(
    snapshot: CoherentSnapshotReview,
    policy: ContextSelectionPolicy,
) -> SyntheticContextBundle:
    """Round-robin already-ranked namespaces; never widen source scope.

    Freshness is only relative to the original coherent snapshot clock.
    The caller must acquire a new snapshot to pick up a later revocation.
    """
    if (
        type(snapshot) is not CoherentSnapshotReview
        or type(policy) is not ContextSelectionPolicy
    ):
        raise PersonalContextReviewRejected("exact context inputs required")
    policy.__post_init__()
    pinned_policy = (
        policy.total_limit, policy.per_namespace_limit, policy.policy_revision,
    )
    if (
        type(snapshot.read_at_ms) is not int
        or not 0 <= snapshot.read_at_ms <= _MAX_INT
        or type(snapshot.scopes) is not tuple
        or type(snapshot.records) is not tuple
        or not 1 <= len(snapshot.scopes) <= 16
        or len(snapshot.scopes) != len(snapshot.records)
        or type(snapshot.provenance_sha256) is not str
        or not _HEX.fullmatch(snapshot.provenance_sha256)
    ):
        raise PersonalContextReviewRejected("coherent snapshot shape changed")
    scopes = snapshot.scopes
    rows = snapshot.records
    if (
        any(type(scope) is not MemoryScope for scope in scopes)
        or len(set((scope.owner_id, scope.namespace) for scope in scopes)) != len(scopes)
        or len({scope.owner_id for scope in scopes}) != 1
    ):
        raise PersonalContextReviewRejected("snapshot owner/namespace boundary invalid")
    # The provenance header and owner/scope identity must remain fixed for the
    # entire projection, including the final content-free hash calculation.
    snapshot_epoch = (snapshot.read_at_ms, snapshot.provenance_sha256)
    scope_epoch = tuple((scope, scope.owner_id, scope.namespace) for scope in scopes)
    record_epoch = []
    pinned = []
    seen: set[str] = set()
    for scope, candidates in zip(scopes, rows, strict=True):
        if type(candidates) is not tuple or len(candidates) > 100:
            raise PersonalContextReviewRejected("snapshot candidate container invalid")
        entries = []
        group_epoch = []
        for record in candidates:
            if type(record) is not MemoryRecord:
                raise PersonalContextReviewRejected("noncanonical memory record")
            if (
                type(record.scope) is not MemoryScope or record.scope != scope
                or type(record.memory_id) is not str
                or type(record.source_id) is not str
                or type(record.content) is not str
                or type(record.content_sha256) is not str
                or not _HEX.fullmatch(record.content_sha256)
                or type(record.revision) is not int or record.revision < 1
                or type(record.created_at_ms) is not int
                or type(record.updated_at_ms) is not int
                or not 0 <= record.created_at_ms <= record.updated_at_ms <= snapshot.read_at_ms
                or record.expires_at_ms is not None
                and (
                    type(record.expires_at_ms) is not int
                    or record.expires_at_ms <= snapshot.read_at_ms
                )
                or hashlib.sha256(record.content.encode("utf-8")).hexdigest()
                != record.content_sha256
            ):
                raise PersonalContextReviewRejected("memory record integrity/freshness changed")
            try:
                expected_id = deterministic_memory_id(scope, record.source_id)
            except (TypeError, ValueError) as exc:
                raise PersonalContextReviewRejected("memory identity is invalid") from exc
            if record.memory_id != expected_id or record.memory_id in seen:
                raise PersonalContextReviewRejected("duplicate or conflicting memory identity")
            seen.add(record.memory_id)
            entries.append((
                record.memory_id, scope.namespace, record.content,
                record.revision, record.content_sha256,
            ))
            group_epoch.append((
                record, record.scope,
                (record.scope.owner_id, record.scope.namespace), record.metadata,
                record.memory_id, record.source_id, record.content,
                record.created_at_ms, record.updated_at_ms,
                record.expires_at_ms, record.revision, record.content_sha256,
                tuple(sorted(record.metadata.items())),
            ))
        pinned.append(tuple(entries))
        record_epoch.append(tuple(group_epoch))
    # A frozen record can be reflectively edited after validation. Comparing
    # only the selected content/revision omits source and owner provenance.
    # Pin all entry identities and the header, including metadata, across
    # both the selection loop and the final digest callback.
    def assert_snapshot_epoch() -> None:
        try:
            stable = (
                pinned_policy == (
                    policy.total_limit, policy.per_namespace_limit,
                    policy.policy_revision,
                )
                and snapshot.scopes is scopes and snapshot.records is rows
                and (snapshot.read_at_ms, snapshot.provenance_sha256) == snapshot_epoch
                and all(
                    current is original
                    and (current.owner_id, current.namespace) == (owner, namespace)
                    for current, (original, owner, namespace) in zip(
                        scopes, scope_epoch, strict=True,
                    )
                )
                and all(
                    record is original
                    and record.scope is record_scope
                    and (record.scope.owner_id, record.scope.namespace) == record_scope_values
                    and record.metadata is metadata
                    and (
                        record.memory_id, record.source_id, record.content,
                        record.created_at_ms, record.updated_at_ms,
                        record.expires_at_ms, record.revision, record.content_sha256,
                    ) == original_values
                    and tuple(sorted(record.metadata.items())) == metadata_values
                    for group, epochs in zip(rows, record_epoch, strict=True)
                    for record, (
                        original, record_scope, record_scope_values, metadata, *saved,
                    ) in zip(group, epochs, strict=True)
                    for original_values, metadata_values in (
                        (tuple(saved[:-1]), saved[-1]),
                    )
                )
            )
        except (AttributeError, TypeError, ValueError):
            stable = False
        if not stable:
            raise PersonalContextReviewRejected("context input changed during selection")


    selected: list[SyntheticContextItem] = []
    counts = [0] * len(scopes)
    for ordinal in range(policy.total_limit):
        chosen = None
        for offset in range(len(scopes)):
            index = (ordinal + offset) % len(scopes)
            if (
                counts[index] < len(pinned[index])
                and counts[index] < policy.per_namespace_limit
            ):
                chosen = index
                break
        if chosen is None:
            break
        memory_id, namespace, content, revision, content_sha = pinned[chosen][
            counts[chosen]
        ]
        counts[chosen] += 1
        # Hashing a selected item is reentrant; a later item must not be
        # able to restore a temporary alteration to source/privacy policy.
        assert_snapshot_epoch()
        provenance = "ctx_" + _hash("ARK-context-provenance-v1", (
            memory_id, namespace, revision, content_sha,
            pinned_policy[2], len(selected),
        ))
        assert_snapshot_epoch()
        selected.append(SyntheticContextItem(
            memory_id, namespace, content, revision, provenance,
        ))
        assert_snapshot_epoch()
    assert_snapshot_epoch()
    # Keep the original selected-item carriers across the final hash and
    # the result constructor. A forged bundle is not privacy clearance.
    selected_items = tuple(selected)
    selected_epoch = tuple((
        item, item.memory_id, item.namespace, item.content,
        item.revision, item.provenance_id,
    ) for item in selected_items)

    def assert_selected_epoch() -> None:
        if len(selected_items) != len(selected_epoch) or any(
            type(item) is not SyntheticContextItem
            or item is not original
            or any(now is not before for now, before in zip(
                (item.memory_id, item.namespace, item.content,
                 item.revision, item.provenance_id),
                (memory_id, namespace, content, revision, provenance),
                strict=True,
            ))
            for item, (
                original, memory_id, namespace, content, revision, provenance,
            ) in zip(selected_items, selected_epoch, strict=True)
        ):
            raise PersonalContextReviewRejected(
                "context selection result changed during bundle construction"
            )

    assert_selected_epoch()
    bundle = "ctx_bundle_" + _hash("ARK-context-bundle-v1", (
        snapshot_epoch[1], pinned_policy,
        tuple(item.provenance_id for item in selected_items),
    ))
    assert_snapshot_epoch()
    assert_selected_epoch()
    result = SyntheticContextBundle(selected_items, bundle, snapshot_epoch[1])
    assert_snapshot_epoch()
    assert_selected_epoch()
    if (
        type(result) is not _BUNDLE_RESULT_TYPE
        or result.items is not selected_items
        or result.bundle_id is not bundle
        or result.snapshot_digest is not snapshot_epoch[1]
    ):
        raise PersonalContextReviewRejected(
            "context bundle result changed during construction"
        )
    return result
