"""Freshness and exact-component gate for disconnected startup probe snapshots.

Synthetic READY assertions are not proof of a functioning local machine,
trusted clock, human consent or ToolBackend safety. This reviewer cannot
grant real execution, notification or hardware access.
"""

from __future__ import annotations

from dataclasses import dataclass

from .startup_readiness_review import ReadinessState, StartupSnapshot

_MAX = 2**63 - 1
_LIMIT = 512


class SyntheticStartupLeaseRejected(RuntimeError):
    """A disconnected readiness lease is missing, stale or inconsistent."""


@dataclass(frozen=True, slots=True)
class SyntheticReadinessRequirement:
    component_id: str
    schema_revision: str

    def assert_shape(self) -> None:
        for label, value in (
            ("component", self.component_id),
            ("schema", self.schema_revision),
        ):
            if type(value) is not str or not value.strip() or len(value) > 256:
                raise SyntheticStartupLeaseRejected(
                    f"invalid exact {label} requirement"
                )


@dataclass(frozen=True, slots=True)
class SyntheticStartupLeaseReview:
    snapshot_digest: str
    required_components: tuple[str, ...]
    captured_at_ms: int
    checked_at_ms: int

    @property
    def startup_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False


def review_synthetic_startup_lease(
    snapshot: StartupSnapshot,
    requirements: tuple[SyntheticReadinessRequirement, ...],
    *,
    captured_at_ms: int,
    now_ms: int,
    max_age_ms: int,
) -> SyntheticStartupLeaseReview:
    """Check current fixture state against a bounded exact dependency contract.

    Caller-supplied clocks and probe values are untrusted. The lease can
    become stale or blocked after review; it is not a capability grant.
    """
    if (
        type(snapshot) is not StartupSnapshot
        or type(requirements) is not tuple
        or not 1 <= len(requirements) <= _LIMIT
        or any(type(item) is not SyntheticReadinessRequirement for item in requirements)
        or any(type(value) is not int for value in (
            captured_at_ms, now_ms, max_age_ms,
        ))
    ):
        raise SyntheticStartupLeaseRejected("exact synthetic lease inputs required")
    if (
        not 0 <= captured_at_ms <= now_ms <= _MAX
        or not 0 <= max_age_ms <= _MAX
        or now_ms - captured_at_ms > max_age_ms
    ):
        raise SyntheticStartupLeaseRejected("synthetic startup lease expired or clock regressed")
    for item in requirements:
        item.assert_shape()
    epoch = tuple((item, item.component_id, item.schema_revision) for item in requirements)
    names = tuple(item.component_id for item in requirements)
    if len(set(names)) != len(names):
        raise SyntheticStartupLeaseRejected("duplicate required readiness component")
    try:
        snapshot._assert_integrity()
        digest = snapshot.digest
        by_name = {entry.component_id: entry for entry in snapshot.components}
        for item in requirements:
            current = by_name.get(item.component_id)
            if current is None:
                raise SyntheticStartupLeaseRejected("required component is not present")
            if (
                current.effective_state is not ReadinessState.READY
                or current.local_state is not ReadinessState.READY
                or current.schema_revision != item.schema_revision
            ):
                raise SyntheticStartupLeaseRejected(
                    "required component blocked, degraded or schema-stale"
                )
        snapshot._assert_integrity()
        if (
            snapshot.digest != digest
            or any(
                type(item) is not SyntheticReadinessRequirement
                or item.component_id != component_id
                or item.schema_revision != revision
                for item, component_id, revision in epoch
            )
        ):
            raise SyntheticStartupLeaseRejected("readiness inputs changed during review")
    except (ValueError, TypeError, AttributeError) as exc:
        raise SyntheticStartupLeaseRejected("startup snapshot integrity rejected") from exc
    return SyntheticStartupLeaseReview(
        digest, tuple(sorted(names)), captured_at_ms, now_ms,
    )
