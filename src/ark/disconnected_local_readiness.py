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

from .agency.contracts import CapabilityGrant, PlanConflictError, StepState
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
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


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
_SCHEMA_TYPE = DisconnectedSQLiteSchemaSeal
_SCHEMA_DENIALS = (
    "source_authenticated", "independent_custody_proven",
    "wal_snapshot_verified", "cross_store_atomicity_proven",
    "application_data_disclosure_authorized",
)
_PREFLIGHT_DENIALS = (
    "dispatch_authorized", "external_result_verified",
    "authenticated_clock_or_consent", "automatic_replay_authorized",
)
_REPORT_DENIALS = (
    "startup_authorized", "dispatch_authorized",
    "source_authenticated", "cross_store_atomicity_proven",
)
# Snapshot descriptors before any SQLite or registered-READ callback. A
# substituted False-returning property must never become the new baseline.
_ORIGINAL_SCHEMA_DENIALS = tuple(vars(_SCHEMA_TYPE)[n] for n in _SCHEMA_DENIALS)
_ORIGINAL_PREFLIGHT_DENIALS = tuple(
    vars(_PREFLIGHT_TYPE)[n] for n in _PREFLIGHT_DENIALS
)
_ORIGINAL_REPORT_DENIALS = tuple(vars(_REPORT_TYPE)[n] for n in _REPORT_DENIALS)
_REPORT_FIELDS = (
    "schema_sha256", "topology_digest", "registry_revision",
    "ready_step_ids", "review_digest",
)
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT_TYPE)[n] for n in _REPORT_FIELDS)
_ORIGINAL_REPORT_INIT = vars(_REPORT_TYPE)["__init__"]

# These frozen receipt slots are read before any schema/registry callback.
# A substituted field getter must never observe caller-owned metadata while
# reporting a harmless unchanged readiness result.
_SCHEMA_CARRIER_NAMES = (
    "schema_sha256", "object_count", "user_version", "schema_version",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_PREFLIGHT_CARRIER_NAMES = (
    "topology_digest", "status_digest", "registry_revision",
    "grant_fingerprint", "ready_step_ids", "ready_bound_ids", "fingerprint",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_ORIGINAL_SCHEMA_CARRIERS = tuple(
    vars(_SCHEMA_TYPE).get(name) for name in _SCHEMA_CARRIER_NAMES
)
_ORIGINAL_PREFLIGHT_CARRIERS = tuple(
    vars(_PREFLIGHT_TYPE).get(name) for name in _PREFLIGHT_CARRIER_NAMES
)


def _require_original_denials() -> None:
    if (
        any(
            vars(_SCHEMA_TYPE).get(name) is not pinned
            for name, pinned in zip(
                _SCHEMA_CARRIER_NAMES, _ORIGINAL_SCHEMA_CARRIERS, strict=True,
            )
        )
        or any(
            vars(_PREFLIGHT_TYPE).get(name) is not pinned
            for name, pinned in zip(
                _PREFLIGHT_CARRIER_NAMES, _ORIGINAL_PREFLIGHT_CARRIERS, strict=True,
            )
        )
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup schema receipt authority carrier changed"
        )
    # The startup review may handle private fixture topology/registry identity.
    # Never send those values into a substituted digest/JSON callback.
    if (
        hashlib is not _ORIGINAL_HASHLIB or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup digest dependencies changed"
        )
    if (
        DisconnectedSQLiteSchemaSeal is not _SCHEMA_TYPE
        or any(
            vars(_SCHEMA_TYPE).get(n) is not old
            for n, old in zip(
                _SCHEMA_DENIALS, _ORIGINAL_SCHEMA_DENIALS, strict=True,
            )
        )
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup schema authority definition changed"
        )
    if (
        DisconnectedReadPreflight is not _PREFLIGHT_TYPE
        or any(
            vars(_PREFLIGHT_TYPE).get(n) is not old
            for n, old in zip(
                _PREFLIGHT_DENIALS, _ORIGINAL_PREFLIGHT_DENIALS, strict=True,
            )
        )
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup READ receipt authority definition changed"
        )
    if (
        DisconnectedLocalReadiness is not _REPORT_TYPE
        or vars(_REPORT_TYPE).get("__init__") is not _ORIGINAL_REPORT_INIT
        or any(
            vars(_REPORT_TYPE).get(n) is not old
            for n, old in zip(
                _REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REPORT_TYPE).get(n) is not old
            for n, old in zip(
                _REPORT_DENIALS, _ORIGINAL_REPORT_DENIALS, strict=True,
            )
        )
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup report authority definition changed"
        )


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
    _require_original_denials()
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
        _require_original_denials()
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
        _require_original_denials()

    def checked_seal_epoch(
        value: object, *, phase: str,
    ) -> tuple[object, ...]:
        # An equal-valued but replaced seal, a duck-typed result, or a
        # source-authorizing descriptor is not a stable startup witness.
        _require_original_denials()
        try:
            if (
                type(value) is not DisconnectedSQLiteSchemaSeal
            ):
                raise DisconnectedLocalReadinessRejected(
                    f"startup {phase} schema authority invalid"
                )
            # An earlier authority read can rebind a later False-only getter.
            # Inspect the original descriptor before EACH individual read.
            for name in _SCHEMA_DENIALS:
                _require_original_denials()
                if getattr(value, name) is not False:
                    raise DisconnectedLocalReadinessRejected(
                        f"startup {phase} schema authority invalid"
                    )
                _require_original_denials()
            return (
                value.schema_sha256, value.object_count,
                value.user_version, value.schema_version,
            )
        except (AttributeError, TypeError, ValueError) as exc:
            if type(exc) is DisconnectedLocalReadinessRejected:
                raise
            raise DisconnectedLocalReadinessRejected(
                f"startup {phase} schema receipt invalid"
            ) from exc

    assert_epoch()
    checked_seal_epoch(retained_schema, phase="retained")
    try:
        first = review_disconnected_sqlite_schema(connection, retained_schema)
    except SQLiteSchemaProbeRejected as exc:
        raise DisconnectedLocalReadinessRejected("startup schema probe denied") from exc
    assert_epoch()
    first_epoch = checked_seal_epoch(first, phase="first")
    if first_epoch != schema_epoch:
        raise DisconnectedLocalReadinessRejected("startup first schema differs")
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
    ):
        raise DisconnectedLocalReadinessRejected("startup READ receipt invalid")
    for name in _PREFLIGHT_DENIALS:
        _require_original_denials()
        if getattr(preview, name) is not False:
            raise DisconnectedLocalReadinessRejected("startup READ receipt invalid")
        _require_original_denials()
    # A returned preflight receipt is a caller-observable Python object, not
    # an independently authenticated authority. Check exact READY membership
    # and registered identities instead of trusting a forged same-type preview.
    try:
        statuses = plan.statuses()
        expected_ready = tuple(
            step_id for step_id in sorted(plan.steps)
            if statuses[step_id].state is StepState.PENDING
            and all(
                statuses[dep].state is StepState.SUCCEEDED
                for dep in plan.steps[step_id].depends_on
            )
        )
        expected_bound = tuple(
            registry.bind(plan.steps[step_id].call).bound_action_id
            for step_id in expected_ready
        )
    except (KeyError, TypeError, ValueError, PlanConflictError) as exc:
        raise DisconnectedLocalReadinessRejected(
            "startup READY identity could not be verified"
        ) from exc
    assert_epoch()
    if (
        preview.ready_step_ids != expected_ready
        or preview.ready_bound_ids != expected_bound
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup READY membership or registry binding changed"
        )

    # Independently recompute the canonical preflight hash from authoritative
    # inputs. A field-shuffled but same-type preflight cannot become readiness.
    def preflight_digest(payload: object) -> str:
        _require_original_denials()
        data = json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        _require_original_denials()
        return hashlib.sha256(
            b"ARK-disconnected-registered-read-preflight-v1\0" + data
        ).hexdigest()

    expected_grants = preflight_digest([
        (grant.capability, grant.scope, grant.expires_at_ms)
        for grant in grants
    ])
    expected_fingerprint = preflight_digest({
        "topology": topology,
        "status": status,
        "registry": revision,
        "grants": expected_grants,
        "clock_observation_ms": observed_at_ms,
        "ready": list(zip(expected_ready, expected_bound, strict=True)),
    })
    assert_epoch()
    if (
        preview.grant_fingerprint != expected_grants
        or preview.fingerprint != expected_fingerprint
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup preflight evidence fingerprint changed"
        )

    preview_epoch = (
        preview.topology_digest, preview.status_digest, preview.registry_revision,
        preview.grant_fingerprint, preview.ready_step_ids,
        preview.ready_bound_ids, preview.fingerprint,
    )

    def assert_preview_epoch() -> None:
        _require_original_denials()
        try:
            current = (
                preview.topology_digest, preview.status_digest,
                preview.registry_revision, preview.grant_fingerprint,
                preview.ready_step_ids, preview.ready_bound_ids,
                preview.fingerprint,
            )
            stable = (
                type(preview) is _PREFLIGHT_TYPE
                and all(
                    value is old for value, old in zip(
                        current, preview_epoch, strict=True,
                    )
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise DisconnectedLocalReadinessRejected(
                "startup READ receipt epoch invalid"
            ) from exc
        if not stable:
            raise DisconnectedLocalReadinessRejected(
                "startup READ receipt epoch changed"
            )
        for name in _PREFLIGHT_DENIALS:
            _require_original_denials()
            if getattr(preview, name) is not False:
                raise DisconnectedLocalReadinessRejected(
                    "startup READ receipt epoch changed"
                )
            _require_original_denials()

    assert_preview_epoch()
    try:
        second = review_disconnected_sqlite_schema(connection, retained_schema)
    except SQLiteSchemaProbeRejected as exc:
        raise DisconnectedLocalReadinessRejected("startup schema changed") from exc
    assert_epoch()
    assert_preview_epoch()
    second_epoch = checked_seal_epoch(second, phase="second")
    # Comparing frozen schema dataclasses via __eq__ would execute a mutable
    # class-level callback. All four exact seal scalars were already checked
    # in both independent reviews; compare their immutable images only.
    # This is a disconnected consistency check, not atomic WAL custody.
    if (
        second_epoch != schema_epoch
        or any(
            current is not old for current, old in zip(
                checked_seal_epoch(first, phase="first"), first_epoch,
                strict=True,
            )
        )
    ):
        raise DisconnectedLocalReadinessRejected("startup schema is not stable")
    _require_original_denials()
    packed = json.dumps(
        (schema_epoch, topology, status, revision, preview.fingerprint,
         preview.ready_step_ids, observed_at_ms),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    _require_original_denials()
    fingerprint = hashlib.sha256(_DOMAIN + packed).hexdigest()
    assert_epoch()
    assert_preview_epoch()
    # Never invoke a late-rebound global constructor even for a deny-only
    # diagnostic report. The pinned import-time type is the sole constructor.
    _require_original_denials()
    report = _REPORT_TYPE(
        retained_schema.schema_sha256, topology, revision,
        preview.ready_step_ids, fingerprint,
    )
    assert_epoch()
    assert_preview_epoch()
    if (
        type(report) is not _REPORT_TYPE
        or report.schema_sha256 is not schema_epoch[0]
        or report.topology_digest is not topology
        or report.registry_revision is not revision
        or report.ready_step_ids is not preview.ready_step_ids
        or report.review_digest is not fingerprint
    ):
        raise DisconnectedLocalReadinessRejected("startup report changed")
    for name in _REPORT_DENIALS:
        _require_original_denials()
        if getattr(report, name) is not False:
            raise DisconnectedLocalReadinessRejected("startup report changed")
        _require_original_denials()
    # The report's False-returning authority getters above can mutate
    # reflected startup inputs or the report itself. Close both epochs after
    # the last authority inspection; this remains diagnostic-only.
    assert_preview_epoch()
    assert_epoch()
    if (
        type(report) is not _REPORT_TYPE
        or report.schema_sha256 is not schema_epoch[0]
        or report.topology_digest is not topology
        or report.registry_revision is not revision
        or report.ready_step_ids is not preview.ready_step_ids
        or report.review_digest is not fingerprint
    ):
        raise DisconnectedLocalReadinessRejected(
            "startup report changed after authority review"
        )
    return report
