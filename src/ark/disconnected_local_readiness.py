"""Disconnected startup review of a caller-opened SQLite schema and READ plan.

This is an opt-in, reversible diagnostic that joins independently tested schema
and registered-READ preflight contracts. It never opens local paths, reads
application rows, starts a ToolBackend, uses a system clock, or grants authority.
Two separated SQLite snapshots do NOT establish cross-store atomicity.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from .agency.contracts import CapabilityGrant, PlanConflictError
from .agency.disconnected_read_preflight import (
    DisconnectedReadPreflight,
    DisconnectedReadPreflightRejected,
    preview_registered_read_plan,
)
from .agency.planner import PlanGraph
from .agency.policy import PermissionGate
from .agency.registry import ToolRegistry
from .disconnected_sqlite_schema_probe import (
    DisconnectedSQLiteSchemaSeal,
    SQLiteSchemaProbeRejected,
    review_disconnected_sqlite_schema,
)

_DOMAIN = b"ARK-disconnected-local-readiness-v1\0"


class DisconnectedLocalReadinessRejected(ValueError):
    """Startup inputs were inconsistent or could not be safely reviewed."""


@dataclass(frozen=True, slots=True)
class DisconnectedLocalReadiness:
    schema_sha256: str
    topology_digest: str
    registry_revision: str
    ready_step_ids: tuple[str, ...]
    review_digest: str

    @property
    def startup_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False


_REPORT_TYPE = DisconnectedLocalReadiness
_PREFLIGHT_TYPE = DisconnectedReadPreflight


def review_disconnected_local_readiness(
    connection: sqlite3.Connection,
    retained_schema: DisconnectedSQLiteSchemaSeal,
    plan: PlanGraph,
    registry: ToolRegistry,
    gate: PermissionGate,
    grants: tuple[CapabilityGrant, ...],
    *,
    observed_at_ms: int,
) -> DisconnectedLocalReadiness:
    """Review metadata and exact registered READ grants without execution."""
    if (
        type(connection) is not sqlite3.Connection
        or type(retained_schema) is not DisconnectedSQLiteSchemaSeal
        or type(plan) is not PlanGraph
        or type(registry) is not ToolRegistry
        or type(gate) is not PermissionGate
        or type(grants) is not tuple
        or len(grants) > 128
        or any(type(grant) is not CapabilityGrant for grant in grants)
        or type(observed_at_ms) is not int
        or not 0 <= observed_at_ms <= 2**63 - 1
    ):
        raise DisconnectedLocalReadinessRejected("invalid exact startup inputs")

    schema_epoch = (
        retained_schema.schema_sha256, retained_schema.object_count,
        retained_schema.user_version, retained_schema.schema_version,
    )
    grant_epoch = tuple(
        (grant, grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    )
    try:
        topology, status, revision = (
            plan.topology_digest(), plan.status_digest(), registry.revision,
        )
    except (TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedLocalReadinessRejected("invalid plan or registry") from exc

    def assert_epoch() -> None:
        try:
            stable = (
                type(retained_schema) is DisconnectedSQLiteSchemaSeal
                and all(
                    value is old for value, old in zip(
                        (retained_schema.schema_sha256, retained_schema.object_count,
                         retained_schema.user_version, retained_schema.schema_version),
                        schema_epoch, strict=True,
                    )
                )
                and plan.topology_digest() == topology
                and plan.status_digest() == status
                and registry.revision == revision
                and all(
                    type(grant) is CapabilityGrant
                    and grant is saved
                    and grant.capability is capability
                    and grant.scope is scope
                    and grant.expires_at_ms is expiry
                    for grant, (saved, capability, scope, expiry) in zip(
                        grants, grant_epoch, strict=True,
                    )
                )
            )
        except (AttributeError, KeyError, TypeError, ValueError, PlanConflictError) as exc:
            raise DisconnectedLocalReadinessRejected("startup epoch changed") from exc
        if not stable:
            raise DisconnectedLocalReadinessRejected("startup epoch changed")

    assert_epoch()
    try:
        first = review_disconnected_sqlite_schema(connection, retained_schema)
    except SQLiteSchemaProbeRejected as exc:
        raise DisconnectedLocalReadinessRejected("startup schema probe denied") from exc
    assert_epoch()
    try:
        preview = preview_registered_read_plan(
            plan, registry, gate, grants, observed_at_ms=observed_at_ms,
        )
    except (DisconnectedReadPreflightRejected, PlanConflictError) as exc:
        raise DisconnectedLocalReadinessRejected("startup READ preflight denied") from exc
    assert_epoch()
    if (
        type(preview) is not _PREFLIGHT_TYPE
        or preview.topology_digest != topology
        or preview.status_digest != status
        or preview.registry_revision != revision
        or type(preview.ready_step_ids) is not tuple
        or type(preview.ready_bound_ids) is not tuple
        or len(preview.ready_step_ids) != len(preview.ready_bound_ids)
        or not preview.ready_step_ids
        or preview.dispatch_authorized is not False
        or preview.external_result_verified is not False
        or preview.authenticated_clock_or_consent is not False
        or preview.automatic_replay_authorized is not False
    ):
        raise DisconnectedLocalReadinessRejected("startup READ receipt invalid")
    try:
        second = review_disconnected_sqlite_schema(connection, retained_schema)
    except SQLiteSchemaProbeRejected as exc:
        raise DisconnectedLocalReadinessRejected("startup schema changed") from exc
    assert_epoch()
    if first != retained_schema or second != first:
        raise DisconnectedLocalReadinessRejected("startup schema is not stable")
    packed = json.dumps(
        (schema_epoch, topology, status, revision, preview.fingerprint,
         preview.ready_step_ids, observed_at_ms),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    fingerprint = hashlib.sha256(_DOMAIN + packed).hexdigest()
    assert_epoch()
    report = DisconnectedLocalReadiness(
        retained_schema.schema_sha256, topology, revision,
        preview.ready_step_ids, fingerprint,
    )
    assert_epoch()
    if (
        type(report) is not _REPORT_TYPE
        or report.schema_sha256 is not schema_epoch[0]
        or report.topology_digest is not topology
        or report.registry_revision is not revision
        or report.ready_step_ids is not preview.ready_step_ids
        or report.review_digest is not fingerprint
        or report.startup_authorized is not False
        or report.dispatch_authorized is not False
        or report.source_authenticated is not False
        or report.cross_store_atomicity_proven is not False
    ):
        raise DisconnectedLocalReadinessRejected("startup report changed")
    return report
