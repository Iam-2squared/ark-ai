"""Offline cross-store WRITE quarantine matrix, never an action decision.

The caller supplies one independently retained complete WRITE-ID list and
observations from separately committed stores. Matching rows and a local hash
are not proof of list completeness, trustworthy storage, or an external effect.
All rows remain non-dispatchable even when every store appears empty.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields

_MAX_STEPS = 128
_MAX_ID_CHARS = 256
_MAX_BYTES = 45_000
_TOPOLOGY = re.compile(r"plan_[0-9a-f]{64}\Z")
_PLAN_STATES = frozenset(("pending", "running", "succeeded", "failed", "blocked"))
_EVIDENCE_STATES = frozenset(("absent", "present", "unavailable"))
_DOMAIN = b"ARK-disconnected-write-quarantine-matrix-v1\0"


class SyntheticQuarantineMatrixRejected(RuntimeError):
    """Cross-store evidence is insufficient even for a bounded diagnostic."""


@dataclass(frozen=True, slots=True)
class SyntheticWriteStoreObservation:
    step_id: str
    plan_state: str
    reservation: str
    preaction_audit: str
    audit_link: str


@dataclass(frozen=True, slots=True)
class SyntheticQuarantineFinding:
    step_id: str
    reasons: tuple[str, ...]

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SyntheticQuarantineMatrix:
    topology_digest: str
    observed_write_step_ids: tuple[str, ...]
    findings: tuple[SyntheticQuarantineFinding, ...]
    local_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def _valid_id(value: object) -> bool:
    if type(value) is not str or not value.strip() or len(value) > _MAX_ID_CHARS:
        return False
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        return False
    return True


def _hash(data: bytes) -> str:
    return "quarantine_" + hashlib.sha256(_DOMAIN + data).hexdigest()


def diagnose_disconnected_write_quarantine(
    *,
    topology_digest: str,
    independently_expected_step_ids: tuple[str, ...],
    observations: tuple[SyntheticWriteStoreObservation, ...],
) -> SyntheticQuarantineMatrix:
    """Classify offline inconsistencies without releasing ANY WRITE for retry.

    The expected list must have been retained outside the recovered stores.
    Do not reconstruct it from the same archive being checked. Unknown states,
    missing evidence, and apparently clean PENDING rows all stay quarantined.
    """
    expected = independently_expected_step_ids
    observed = observations
    original_topology = topology_digest
    if (
        type(original_topology) is not str
        or _TOPOLOGY.fullmatch(original_topology) is None
        or type(expected) is not tuple
        or type(observed) is not tuple
        or not 1 <= len(expected) <= _MAX_STEPS
        or len(observed) != len(expected)
        or any(not _valid_id(name) for name in expected)
        or expected != tuple(sorted(set(expected)))
        or any(type(row) is not SyntheticWriteStoreObservation for row in observed)
    ):
        raise SyntheticQuarantineMatrixRejected("invalid independent WRITE matrix")

    pinned_rows = tuple(
        (row, tuple(getattr(row, item.name) for item in fields(row)))
        for row in observed
    )

    def assert_epoch() -> None:
        if (
            topology_digest is not original_topology
            or independently_expected_step_ids is not expected
            or observations is not observed
            or len(observed) != len(pinned_rows)
            or any(
                row is not original
                or any(
                    getattr(row, item.name) is not value
                    for item, value in zip(fields(row), values, strict=True)
                )
                for row, (original, values) in zip(
                    observed, pinned_rows, strict=True,
                )
            )
        ):
            raise SyntheticQuarantineMatrixRejected("WRITE evidence changed during diagnosis")

    assert_epoch()
    encoded_rows = []
    findings = []
    for name, row in zip(expected, observed, strict=True):
        assert_epoch()
        if (
            row.step_id != name
            or type(row.plan_state) is not str
            or row.plan_state not in _PLAN_STATES
            or any(
                type(state) is not str or state not in _EVIDENCE_STATES
                for state in (row.reservation, row.preaction_audit, row.audit_link)
            )
        ):
            raise SyntheticQuarantineMatrixRejected("missing or mismatched WRITE evidence")
        reasons = ["no_external_nonexecution_proof"]
        if row.plan_state == "running":
            reasons.append("planner_running_uncertain")
        elif row.plan_state in ("succeeded", "failed", "blocked"):
            reasons.append("planner_terminal_unverified")
        if "unavailable" in (row.reservation, row.preaction_audit, row.audit_link):
            reasons.append("store_unavailable")
        if row.reservation == "present":
            reasons.append("reservation_already_persisted")
        if row.preaction_audit == "present":
            reasons.append("preaction_audit_recorded")
        if row.audit_link == "present":
            reasons.append("audit_link_recorded")
            if row.reservation == "absent" or row.preaction_audit == "absent":
                reasons.append("cross_store_orphan")
        findings.append(SyntheticQuarantineFinding(name, tuple(reasons)))
        encoded_rows.append((
            name, row.plan_state, row.reservation,
            row.preaction_audit, row.audit_link,
        ))
        assert_epoch()

    payload = json.dumps(
        [original_topology, list(expected), encoded_rows],
        ensure_ascii=True, separators=(",", ":"),
    ).encode("utf-8")
    if len(payload) > _MAX_BYTES:
        raise SyntheticQuarantineMatrixRejected("WRITE matrix budget exceeded")
    assert_epoch()
    local_digest = _hash(payload)
    assert_epoch()
    result = SyntheticQuarantineMatrix(
        original_topology, expected, tuple(findings), local_digest,
    )
    assert_epoch()
    if (
        type(result) is not SyntheticQuarantineMatrix
        or result.topology_digest is not original_topology
        or result.observed_write_step_ids is not expected
        or type(result.findings) is not tuple
        or len(result.findings) != len(expected)
        or result.local_digest is not local_digest
    ):
        raise SyntheticQuarantineMatrixRejected("WRITE diagnostic result changed")
    return result
