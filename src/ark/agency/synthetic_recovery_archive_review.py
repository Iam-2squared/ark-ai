"""Content-minimized, caller-retained synthetic recovery archive for restart.

This is an inert, canonical JSON checkpoint of local witness values. It must be
preserved independently of the three/four SQLite stores to detect rollback.
Neither a digest nor a matching restart review authenticates a human approval,
external WRITE outcome, backend idempotency or real exactly-once semantics.
No filesystem writes, ToolBackend calls or automatic retries occur here.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields
from pathlib import Path

from .audit import SQLiteActionAudit
from .audit_continuity_review import AuditContinuityWitness
from .contracts import StepState, ToolCall
from .planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail
from .registry import ToolRegistry
from .synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkWitness,
    SyntheticOccurrenceAuditLinkStore,
)
from .synthetic_occurrence_continuity_review import SyntheticLedgerWitness
from .synthetic_recovery_triage import (
    SyntheticRecoveryReview,
    review_synthetic_write_recovery,
)

_LABEL = b"ARK-synthetic-recovery-archive-v1\0"
_MAX_BYTES = 4_000_000
_ALLOWED_STATES = frozenset(state.value for state in StepState)
_OCCURRENCE_ID = re.compile(r"occ_[0-9a-f]{64}$")


class SyntheticRecoveryArchiveRejected(RuntimeError):
    """An offline recovery archive cannot be trusted even as local evidence."""


@dataclass(frozen=True, slots=True)
class SyntheticRecoveryArchive:
    """Opaque canonical snapshot; retaining it independently is caller work."""

    canonical_json: bytes
    digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _digest(data: bytes) -> str:
    return "srecovery_" + hashlib.sha256(_LABEL + data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _fields(value: object, names: tuple[str, ...]) -> dict[str, object]:
    return {name: getattr(value, name) for name in names}


_PLAN = (
    "topology_digest", "event_count", "event_hash",
    "status_digest", "last_at_ms",
)
_AUDIT = ("event_count", "tail_event_id", "chain_sha256")
_LINK = ("event_count", "tail_hash", "last_link_at_ms")


def _check_keys(value: object, keys: tuple[str, ...]) -> dict:
    if type(value) is not dict or set(value) != set(keys):
        raise SyntheticRecoveryArchiveRejected("archive shape changed")
    return value


def _restore(archive: SyntheticRecoveryArchive) -> tuple:
    """Strictly validate all detached local witnesses without opening a DB."""
    if (
        type(archive) is not SyntheticRecoveryArchive
        or type(archive.canonical_json) is not bytes
        or not 0 < len(archive.canonical_json) <= _MAX_BYTES
        or type(archive.digest) is not str
        or archive.digest != _digest(archive.canonical_json)
    ):
        raise SyntheticRecoveryArchiveRejected("archive bytes or digest changed")
    try:
        payload = json.loads(archive.canonical_json)
        if _canonical(payload) != archive.canonical_json:
            raise SyntheticRecoveryArchiveRejected("noncanonical recovery archive")
        _check_keys(payload, (
            "version", "identity", "plan", "ledger", "audit", "link",
            "occurrences", "audit_links",
        ))
        if type(payload["version"]) is not int or payload["version"] != 1:
            raise SyntheticRecoveryArchiveRejected("unsupported archive version")
        identity = _check_keys(payload["identity"], (
            "step_id", "request_id", "registry_revision", "bound_action_id",
            "step_state", "ambiguous_write",
        ))
        if (
            any(type(identity[k]) is not str or not identity[k] for k in (
                "step_id", "request_id", "registry_revision", "bound_action_id",
            ))
            or type(identity["step_state"]) is not str
            or identity["step_state"] not in _ALLOWED_STATES
            or type(identity["ambiguous_write"]) is not bool
        ):
            raise SyntheticRecoveryArchiveRejected("archive identity is malformed")
        # Recovery marks precisely the RUNNING state as ambiguous. An archive
        # may not detach its externally unknown WRITE flag from that state.
        if identity["ambiguous_write"] != (
            identity["step_state"] == StepState.RUNNING.value
        ):
            raise SyntheticRecoveryArchiveRejected(
                "archive ambiguity contradicts planner state"
            )
        plan = SyntheticPlanTail(**_check_keys(payload["plan"], _PLAN))
        plan.assert_shape()
        ledger_data = _check_keys(payload["ledger"], ("row_hashes", "digest"))
        if (
            type(ledger_data["row_hashes"]) is not list
            or len(ledger_data["row_hashes"]) > 10000
        ):
            raise SyntheticRecoveryArchiveRejected("archive ledger is malformed")
        ledger = SyntheticLedgerWitness(
            tuple(ledger_data["row_hashes"]), ledger_data["digest"],
        )
        ledger.assert_integrity()
        audit = AuditContinuityWitness(**_check_keys(payload["audit"], _AUDIT))
        link = None
        if payload["link"] is not None:
            link = SyntheticAuditLinkWitness(
                **_check_keys(payload["link"], _LINK)
            )
            link.assert_shape()
        occurrences = payload["occurrences"]
        links = payload["audit_links"]
        if (
            type(occurrences) is not list
            or len(occurrences) > 10000
            or any(
                type(item) is not str or _OCCURRENCE_ID.fullmatch(item) is None
                for item in occurrences
            )
            or len(set(occurrences)) != len(occurrences)
            or type(links) is not list
            or len(links) > 10000
            or any(
                type(item) is not list or len(item) != 2
                or type(item[0]) is not str or not item[0]
                or type(item[1]) is not int or item[1] < 1
                for item in links
            )
            or len({(item[0], item[1]) for item in links}) != len(links)
            or len({item[0] for item in links}) != len(links)
            or len({item[1] for item in links}) != len(links)
            or any(item[0] not in occurrences for item in links)
            or links and link is None
        ):
            raise SyntheticRecoveryArchiveRejected(
                "archive occurrence references are malformed"
            )
        return (
            identity, plan, ledger, audit, link,
            tuple(occurrences), tuple((item[0], item[1]) for item in links),
        )
    except SyntheticRecoveryArchiveRejected:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError, RuntimeError) as exc:
        raise SyntheticRecoveryArchiveRejected("invalid recovery archive") from exc


def archive_synthetic_recovery(
    review: SyntheticRecoveryReview,
) -> SyntheticRecoveryArchive:
    """Snapshot only review identities/witnesses; never serialize raw ToolCall."""
    if (
        type(review) is not SyntheticRecoveryReview
        or type(review.plan_tail) is not SyntheticPlanTail
        or type(review.ledger_witness) is not SyntheticLedgerWitness
        or type(review.audit_witness) is not AuditContinuityWitness
        or review.link_witness is not None
        and type(review.link_witness) is not SyntheticAuditLinkWitness
    ):
        raise SyntheticRecoveryArchiveRejected("exact recovery review required")
    # Frozen review objects remain reflectively mutable in Python.
    # Pin original carriers of the review and all nested witnesses before
    # any serialization or hashing callbacks can rewrite them.
    originals = tuple(
        (
            entity,
            tuple((field.name, getattr(entity, field.name)) for field in fields(entity)),
        )
        for entity in (
            review, review.plan_tail, review.ledger_witness,
            review.audit_witness, review.link_witness,
        )
        if entity is not None
    )

    def assert_review_epoch() -> None:
        if any(
            getattr(entity, name) is not original
            for entity, values in originals
            for name, original in values
        ):
            raise SyntheticRecoveryArchiveRejected(
                "recovery review changed during archive capture"
            )

    assert_review_epoch()
    payload = {
        "version": 1,
        "identity": _fields(review, (
            "step_id", "request_id", "registry_revision", "bound_action_id",
            "step_state", "ambiguous_write",
        )),
        "plan": _fields(review.plan_tail, _PLAN),
        "ledger": {
            "row_hashes": list(review.ledger_witness.row_hashes),
            "digest": review.ledger_witness.digest,
        },
        "audit": _fields(review.audit_witness, _AUDIT),
        "link": (
            None if review.link_witness is None
            else _fields(review.link_witness, _LINK)
        ),
        "occurrences": list(review.matching_occurrences),
        "audit_links": [list(pair) for pair in review.matching_audit_links],
    }
    try:
        assert_review_epoch()
        data = _canonical(payload)
        assert_review_epoch()
        digest = _digest(data)
        assert_review_epoch()
        archive = SyntheticRecoveryArchive(data, digest)
        _restore(archive)
        assert_review_epoch()
        if archive.canonical_json is not data or archive.digest is not digest:
            raise SyntheticRecoveryArchiveRejected(
                "recovery archive changed during capture validation"
            )
        return archive
    except (TypeError, ValueError, AttributeError, OverflowError) as exc:
        raise SyntheticRecoveryArchiveRejected("cannot snapshot recovery review") from exc


def recheck_synthetic_recovery_archive(
    archive: SyntheticRecoveryArchive,
    journal: SyntheticPlanJournal,
    ledger_path: Path,
    audit: SQLiteActionAudit,
    registry: ToolRegistry,
    call: ToolCall,
    *,
    link_store: SyntheticOccurrenceAuditLinkStore | None = None,
) -> SyntheticRecoveryReview:
    """Reopen independent stores through the existing fail-closed reviewer.

    Append-only local continuations may be visible, but no matching evidence
    can convert an unknown external WRITE into success or permission to retry.
    The caller must independently custody the canonical_json and digest.
    """
    original_bytes = archive.canonical_json if type(archive) is SyntheticRecoveryArchive else None
    original_digest = archive.digest if type(archive) is SyntheticRecoveryArchive else None
    identity, plan, ledger, audit_witness, link, occurrences, links = _restore(archive)
    if link is not None and link_store is None:
        raise SyntheticRecoveryArchiveRejected("retained link requires link store")
    fresh = review_synthetic_write_recovery(
        journal, ledger_path, audit, registry, call,
        step_id=identity["step_id"], retained_plan=plan,
        retained_ledger=ledger, retained_audit=audit_witness,
        link_store=link_store, retained_link=link,
    )
    # A callback may replace the original archive itself during all the reads.
    if (
        archive.canonical_json is not original_bytes
        or archive.digest != original_digest
    ):
        raise SyntheticRecoveryArchiveRejected("archive changed during restart review")
    _restore(archive)
    # A retained RUNNING/UNKNOWN WRITE cannot become known simply because a
    # later local planner journal claims success, failure or cancellation.
    # A synthetic status is not a verified external side-effect receipt.
    if identity["ambiguous_write"] and not fresh.ambiguous_write:
        raise SyntheticRecoveryArchiveRejected(
            "archived UNKNOWN WRITE cannot be resolved by local journal"
        )
    if (
        fresh.step_id != identity["step_id"]
        or fresh.request_id != identity["request_id"]
        or fresh.registry_revision != identity["registry_revision"]
        or fresh.bound_action_id != identity["bound_action_id"]
        or not set(occurrences).issubset(fresh.matching_occurrences)
        or not set(links).issubset(fresh.matching_audit_links)
    ):
        raise SyntheticRecoveryArchiveRejected(
            "reopened recovery differs from retained action identity"
        )
    return fresh
