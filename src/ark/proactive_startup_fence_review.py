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


_RESULT_TYPE = SyntheticProactiveStartupReview
_ORIGINAL_FIELDS_FN = fields
_AUTHORITY_NAMES = (
    "startup_authorized", "notification_authorized",
    "dispatch_authorized", "automatic_replay_authorized",
)
_ORIGINAL_AUTHORITY = tuple(
    vars(_RESULT_TYPE)[name] for name in _AUTHORITY_NAMES
)
# The diagnostic result is constructed only after two separate, potentially
# reentrant SQLite/readiness reviews. Pin its actual class-level constructors,
# slots and lookup hooks at import time, not after consuming private inputs.
_RESULT_FIELDS = (
    "trigger_id", "readiness_digest", "trigger_history_digest",
    "checked_at_ms",
)
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_CARRIER = tuple(
    vars(_RESULT_TYPE).get(name)
    for name in (*_RESULT_FIELDS, *_RESULT_HOOKS)
)

# The combined reviewer reads fields from six independently frozen local
# receipt types. Reject executable class-level getters *before* the first
# provenance/clock/SQLite callback, not only in the child reviewers.
# This is interpreter-local descriptor custody, never authenticated readiness.
_SOURCE_TYPES = (
    SyntheticTriggerReceipt, SyntheticTriggerPolicy, SyntheticTriggerWitness,
    StartupSnapshot, ComponentResult, SyntheticReadinessRequirement,
)
_SOURCE_FIELDS = tuple(
    tuple(item.name for item in fields(cls)) for cls in _SOURCE_TYPES
)
_SOURCE_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_SOURCE_DESCRIPTORS = tuple(
    tuple(vars(cls).get(name) for name in (*names, *_SOURCE_HOOKS))
    for cls, names in zip(_SOURCE_TYPES, _SOURCE_FIELDS, strict=True)
)


def _require_original_authorities() -> None:
    # False-valued replaced properties can execute arbitrary callbacks.
    # Reject the substitution before reading trigger metadata or SQLite.
    if (
        SyntheticProactiveStartupReview is not _RESULT_TYPE
        or fields is not _ORIGINAL_FIELDS_FN
        or _epoch is not _ORIGINAL_EPOCH_FN
        or _snapshot_epoch is not _ORIGINAL_SNAPSHOT_EPOCH_FN
        or (
            SyntheticTriggerReceipt, SyntheticTriggerPolicy,
            SyntheticTriggerWitness, StartupSnapshot, ComponentResult,
            SyntheticReadinessRequirement,
        ) != _SOURCE_TYPES
        or any(
            tuple(vars(cls).get(name) for name in (*names, *_SOURCE_HOOKS))
            != original
            for cls, names, original in zip(
                _SOURCE_TYPES, _SOURCE_FIELDS, _SOURCE_DESCRIPTORS,
                strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                (*_RESULT_FIELDS, *_RESULT_HOOKS),
                _ORIGINAL_RESULT_CARRIER, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _AUTHORITY_NAMES, _ORIGINAL_AUTHORITY, strict=True,
            )
        )
    ):
        raise SyntheticProactiveStartupRejected(
            "proactive authority descriptor epoch changed before review"
        )


def _epoch(value: object, carrier: type) -> tuple[object, ...]:
    return tuple(getattr(value, field.name) for field in fields(carrier))


_ORIGINAL_EPOCH_FN = _epoch


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


_ORIGINAL_SNAPSHOT_EPOCH_FN = _snapshot_epoch


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
    _require_original_authorities()
    # A Path subclass can execute user-defined parents/resolve/stat hooks.
    # Do not read any private readiness/receipt fields until the offline
    # trigger source has an inert exact local pathlib carrier.
    source_epoch = ledger.path
    if type(source_epoch) is not type(Path(".")):
        raise SyntheticProactiveStartupRejected(
            "exact local startup trigger source required"
        )
    pinned = (
        _epoch(receipt, SyntheticTriggerReceipt),
        _epoch(policy, SyntheticTriggerPolicy),
        tuple((item, item.component_id, item.schema_revision) for item in requirements),
        _snapshot_epoch(snapshot),
        source_epoch,
        source_digest,
        observation_digest,
    )
    # A Path compares equal to a newly constructed Path with the same string.
    # Value-only `pinned` therefore cannot detect an inter-pass redirection.
    retained_epoch = None if retained is None else (retained.row_hashes, retained.digest)
    retained_hash_carriers = (
        () if retained is None else tuple(retained.row_hashes)
    )
    # Independent readiness and trigger readers are separate callbacks.
    # Preserve the ORIGINAL snapshot/component carriers across both, not
    # merely their digest-equivalent values checked at the very end.
    snapshot_components = snapshot.components
    snapshot_digest = snapshot.digest
    snapshot_carriers = tuple(
        (item, _epoch(item, ComponentResult)) for item in snapshot_components
    )

    def assert_source_epoch() -> None:
        _require_original_authorities()
        # Both independent reviewers are reentrant. Check the ORIGINAL trigger,
        # policy and requirement carriers after EACH review, not only at the
        # last combined comparison, where a later callback could restore them.
        receipt_fields = _epoch(receipt, SyntheticTriggerReceipt)
        policy_fields = _epoch(policy, SyntheticTriggerPolicy)
        if (
            ledger.path is not source_epoch
            or retained is not None and (
                retained.row_hashes is not retained_epoch[0]
                or retained.digest is not retained_epoch[1]
                or any(
                    current is not original for current, original in zip(
                        retained.row_hashes, retained_hash_carriers, strict=True,
                    )
                )
            )
            or snapshot.components is not snapshot_components
            or snapshot.digest is not snapshot_digest
            or len(snapshot.components) != len(snapshot_carriers)
            or any(
                current is not original
                or any(
                    actual is not pinned_field
                    for actual, pinned_field in zip(
                        _epoch(current, ComponentResult),
                        original_fields, strict=True,
                    )
                )
                for current, (original, original_fields) in zip(
                    snapshot.components, snapshot_carriers, strict=True,
                )
            )
            or len(receipt_fields) != len(pinned[0])
            or any(
                actual is not original for actual, original in zip(
                    receipt_fields, pinned[0], strict=True,
                )
            )
            or len(policy_fields) != len(pinned[1])
            or any(
                actual is not original for actual, original in zip(
                    policy_fields, pinned[1], strict=True,
                )
            )
            or len(requirements) != len(pinned[2])
            or any(
                item is not original
                or item.component_id is not component_id
                or item.schema_revision is not schema_revision
                for item, (original, component_id, schema_revision) in zip(
                    requirements, pinned[2], strict=True,
                )
            )
        ):
            raise SyntheticProactiveStartupRejected(
                "startup trigger input, source or retained evidence changed during review"
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
    # A frozen result constructor is still a reentrant boundary. Keep the
    # previously reviewed receipt digests and exact scalar carriers stable,
    # including after returning the newly constructed diagnostic.
    expected_result = (
        first_trigger.trigger_id, first_ready.snapshot_digest,
        first_trigger.history.digest, now_ms,
    )
    result = SyntheticProactiveStartupReview(*expected_result)
    assert_source_epoch()
    try:
        snapshot._assert_integrity()
        current_result = (
            first_trigger.trigger_id, first_ready.snapshot_digest,
            first_trigger.history.digest, now_ms,
        )
        actual_result = (
            result.trigger_id, result.readiness_digest,
            result.trigger_history_digest, result.checked_at_ms,
        )
        if (
            type(result) is not SyntheticProactiveStartupReview
            or _snapshot_epoch(snapshot) != pinned[3]
            or any(
                current is not original
                for current, original in zip(
                    current_result, expected_result, strict=True,
                )
            )
            or any(
                actual is not original
                for actual, original in zip(
                    actual_result, expected_result, strict=True,
                )
            )
        ):
            raise SyntheticProactiveStartupRejected(
                "constructed proactive readiness result changed"
            )
    except (AttributeError, TypeError, ValueError) as exc:
        raise SyntheticProactiveStartupRejected(
            "constructed proactive readiness result malformed"
        ) from exc
    # Every synthetic READY result is a denial-only diagnostic. These
    # properties can be overridden by reentrant fixture callbacks; reject
    # both truthy "grants" and false-valued getters that change source
    # evidence or the result AFTER the constructor's earlier checks.
    for name in (
        "startup_authorized", "notification_authorized",
        "dispatch_authorized", "automatic_replay_authorized",
    ):
        try:
            denied = getattr(result, name)
        except (AttributeError, TypeError, ValueError) as exc:
            raise SyntheticProactiveStartupRejected(
                "final proactive authority getter failed"
            ) from exc
        if denied is not False:
            raise SyntheticProactiveStartupRejected(
                "final proactive readiness gained execution authority"
            )
        assert_source_epoch()
    try:
        snapshot._assert_integrity()
    except (ValueError, TypeError, AttributeError) as exc:
        raise SyntheticProactiveStartupRejected(
            "startup snapshot changed during final authority denial"
        ) from exc
    assert_source_epoch()
    final_sources = (
        first_trigger.trigger_id, first_ready.snapshot_digest,
        first_trigger.history.digest, now_ms,
    )
    final_result = (
        result.trigger_id, result.readiness_digest,
        result.trigger_history_digest, result.checked_at_ms,
    )
    if (
        type(result) is not SyntheticProactiveStartupReview
        or any(now is not prior for now, prior in zip(
            final_sources, expected_result, strict=True,
        ))
        or any(now is not prior for now, prior in zip(
            final_result, expected_result, strict=True,
        ))
    ):
        raise SyntheticProactiveStartupRejected(
            "final proactive readiness witness changed after denial"
        )
    return result
