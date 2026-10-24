"""Deny-only proactive trigger and startup readiness cross-check.

Prepared scheduler state and caller-supplied READY probes cannot authenticate
a person, deliver a notification, or provide ToolBackend execution authority.
Two independent reads are not a transaction and leave a post-check race.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .proactive_synthetic_continuity_review import SyntheticTriggerWitness
from .proactive_synthetic_freshness_review import review_prepared_trigger_freshness
from .proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
)
from .startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    review_synthetic_startup_lease,
)
from .startup_readiness_review import ComponentResult, StartupSnapshot


class SyntheticProactiveStartupRejected(RuntimeError):
    """A local trigger/readiness review cannot be correlated safely."""


@dataclass(frozen=True, slots=True)
class SyntheticProactiveStartupReview:
    """Diagnostic hashes only; no dispatch, notification, or replay authority."""

    trigger_id: str
    readiness_digest: str
    trigger_history_digest: str
    checked_at_ms: int

    @property
    def startup_authorized(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _epoch(value: object, carrier: type) -> tuple[object, ...]:
    return tuple(getattr(value, field.name) for field in fields(carrier))


def _snapshot_epoch(snapshot: StartupSnapshot) -> tuple[object, ...]:
    """Pin nested component VALUES against reflective changes during a trigger read."""
    if type(snapshot.components) is not tuple or any(
        type(item) is not ComponentResult for item in snapshot.components
    ):
        raise SyntheticProactiveStartupRejected("exact snapshot component types required")
    return (
        snapshot.digest,
        tuple((
            item.component_id, item.dependencies, item.local_state,
            item.effective_state, item.failure_code, item.schema_revision,
        ) for item in snapshot.components),
    )


def review_synthetic_proactive_startup(
    ledger: SyntheticProactiveLedger,
    receipt: SyntheticTriggerReceipt,
    policy: SyntheticTriggerPolicy,
    snapshot: StartupSnapshot,
    requirements: tuple[SyntheticReadinessRequirement, ...],
    *,
    source_digest: str,
    observation_digest: str,
    captured_at_ms: int,
    now_ms: int,
    max_startup_age_ms: int,
    max_observation_age_ms: int,
    retained: SyntheticTriggerWitness | None = None,
) -> SyntheticProactiveStartupReview:
    """Bracket local readiness and durable trigger freshness with repeat reads.

    Every "READY" and "fresh" assertion remains unauthenticated synthetic
    input. A successful return is never permission to notify or execute.
    """
    if (
        type(ledger) is not SyntheticProactiveLedger
        or type(receipt) is not SyntheticTriggerReceipt
        or type(policy) is not SyntheticTriggerPolicy
        or type(snapshot) is not StartupSnapshot
        or type(requirements) is not tuple
        or any(type(item) is not SyntheticReadinessRequirement for item in requirements)
        or retained is not None and type(retained) is not SyntheticTriggerWitness
    ):
        raise SyntheticProactiveStartupRejected("exact synthetic proactive readiness inputs")
    pinned = (
        _epoch(receipt, SyntheticTriggerReceipt),
        _epoch(policy, SyntheticTriggerPolicy),
        tuple((item, item.component_id, item.schema_revision) for item in requirements),
        _snapshot_epoch(snapshot),
        ledger.path,
        source_digest,
        observation_digest,
    )
    # A Path compares equal to a newly constructed Path with the same string.
    # Value-only `pinned` therefore cannot detect an inter-pass redirection.
    source_epoch = ledger.path
    if not isinstance(source_epoch, Path):
        raise SyntheticProactiveStartupRejected("exact startup trigger source required")
    retained_epoch = None if retained is None else (retained.row_hashes, retained.digest)

    def assert_source_epoch() -> None:
        if (
            ledger.path is not source_epoch
            or retained_epoch != (
                None if retained is None else (retained.row_hashes, retained.digest)
            )
        ):
            raise SyntheticProactiveStartupRejected(
                "startup trigger source or retained evidence changed during review"
            )

    readiness_kwargs = {
        "captured_at_ms": captured_at_ms,
        "now_ms": now_ms,
        "max_age_ms": max_startup_age_ms,
    }
    trigger_kwargs = {
        "source_digest": source_digest,
        "observation_digest": observation_digest,
        "now_ms": now_ms,
        "max_observation_age_ms": max_observation_age_ms,
        "retained": retained,
    }
    first_ready = review_synthetic_startup_lease(
        snapshot, requirements, **readiness_kwargs,
    )
    assert_source_epoch()
    first_trigger = review_prepared_trigger_freshness(
        ledger, receipt, policy, **trigger_kwargs,
    )
    assert_source_epoch()
    last_ready = review_synthetic_startup_lease(
        snapshot, requirements, **readiness_kwargs,
    )
    assert_source_epoch()
    last_trigger = review_prepared_trigger_freshness(
        ledger, receipt, policy, **trigger_kwargs,
    )
    assert_source_epoch()
    # No more callbacks below this point should precede the final integrity
    # check. The earlier readiness lease does not cover a late trigger callback.
    try:
        snapshot._assert_integrity()
    except (ValueError, TypeError, AttributeError) as exc:
        raise SyntheticProactiveStartupRejected(
            "startup snapshot changed after readiness review"
        ) from exc
    if (
        first_ready != last_ready
        or first_trigger != last_trigger
        or (
            _epoch(receipt, SyntheticTriggerReceipt),
            _epoch(policy, SyntheticTriggerPolicy),
            tuple((item, item.component_id, item.schema_revision) for item in requirements),
            _snapshot_epoch(snapshot),
            ledger.path,
            source_digest,
            observation_digest,
        ) != pinned
        or first_ready.checked_at_ms != first_trigger.checked_at_ms
    ):
        raise SyntheticProactiveStartupRejected(
            "startup or trigger evidence changed during disconnected review"
        )
    assert_source_epoch()
    return SyntheticProactiveStartupReview(
        first_trigger.trigger_id, first_ready.snapshot_digest,
        first_trigger.history.digest, now_ms,
    )
