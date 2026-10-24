"""Fault-injection-only synthetic WRITE sequence; never dispatches a tool.

The journal, reservation ledger and audit are three independent databases.
An injected stop can leave a RUNNING/UNKNOWN WRITE; callers MUST NOT retry it.
Neither an audit row nor an in-memory mock marker proves a real side effect.
No registered backend method is ever called by this module.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .audit import SQLiteActionAudit
from .contracts import ActionAuditEvent, Effect, OneShotAuthorization, StepState, ToolCall
from .durable_occurrence_review import SyntheticOccurrenceStore
from .planner import PlanGraph
from .planner_journal_review import SyntheticPlanJournal
from .registry import ToolRegistry
from .synthetic_occurrence_audit_link_review import SyntheticOccurrenceAuditLinkStore

_MAX = 2**63 - 1
_FAULTS = frozenset((
    "after_running", "after_reservation", "after_pre_action_audit",
    "after_mock_marker", "after_audit_link",
))


class SyntheticMockCycleRejected(RuntimeError):
    """A synthetic cycle is invalid or would retry an ambiguous WRITE."""


class SyntheticMockCrashInjected(RuntimeError):
    """An artificial stop after a durable boundary; not a process crash."""


@dataclass(frozen=True, slots=True)
class SyntheticMockCycleReceipt:
    step_id: str
    occurrence_id: str
    audit_event_id: int
    mock_marker: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_known(self) -> bool:
        return False


def run_synthetic_mock_cycle(
    journal: SyntheticPlanJournal,
    ledger: SyntheticOccurrenceStore,
    audit: SQLiteActionAudit,
    registry: ToolRegistry,
    call: ToolCall,
    token: OneShotAuthorization,
    *,
    step_id: str,
    occurrence_id: str,
    now_ms: int,
    fault_at: str | None = None,
    link_store: SyntheticOccurrenceAuditLinkStore | None = None,
) -> SyntheticMockCycleReceipt:
    """Drive durable fixture steps in order, with no backend access.

    PENDING -> RUNNING is journaled first, then a synthetic occurrence is
    reserved, then a pre-action audit row is committed, then a deterministic
    in-memory marker is computed. No actual action is performed. Failure at
    any point leaves a write that this API will refuse to replay.
    """
    if (
        type(journal) is not SyntheticPlanJournal
        or type(ledger) is not SyntheticOccurrenceStore
        or type(audit) is not SQLiteActionAudit
        or type(registry) is not ToolRegistry
        or type(call) is not ToolCall
        or type(token) is not OneShotAuthorization
        or type(step_id) is not str or not step_id
        or type(occurrence_id) is not str
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        or fault_at is not None and (
            type(fault_at) is not str or fault_at not in _FAULTS
        )
        or link_store is not None and type(link_store) is not SyntheticOccurrenceAuditLinkStore
    ):
        raise SyntheticMockCycleRejected("exact synthetic mock inputs required")
    if fault_at == "after_audit_link" and link_store is None:
        raise SyntheticMockCycleRejected("audit-link stop requires a synthetic sidecar")
    # Pin exact, independently held fixture inputs before registry callbacks
    # and before the FIRST cross-SQLite durable transition. All stores remain
    # separate: a detected drift AFTER RUNNING leaves an UNKNOWN, not a retry.
    original_paths = (
        journal._path, ledger._path, audit.path,
        link_store._path if link_store is not None else None,
    )
    if any(not isinstance(p, Path) for p in original_paths if p is not None):
        raise SyntheticMockCycleRejected("mock sources require stable Path objects")
    original_call = (
        call.tool, call.capability, call.scope, call.arguments, call.request_id,
    )
    original_token = (token.token_id, token.request_id, token.expires_at_ms)
    original_steps = journal._steps
    original_step_fields = tuple(
        (entry, entry.step_id, entry.call, entry.depends_on,
         entry.call.request_id)
        for entry in original_steps
    )
    bound = registry.bind(call)

    bound_epoch = (
        bound.registry_revision, bound.bound_action_id,
        bound.registration, bound.call,
    )

    def assert_identity_epoch() -> None:
        # Registry binding is a callback too. Checking local inputs only
        # BEFORE that callback could accept a changed token or source until
        # the next phase, possibly after a durable reservation is written.
        def local_stable() -> bool:
            paths = (
                journal._path, ledger._path, audit.path,
                link_store._path if link_store is not None else None,
            )
            steps = journal._steps
            return (
                all(new is old for new, old in zip(
                    paths, original_paths, strict=True,
                ))
                and steps is original_steps
                and len(steps) == len(original_step_fields)
                and all(
                    entry is original and entry.step_id == step_id
                    and entry.call is old_call
                    and entry.depends_on is deps
                    and entry.call.request_id == request_id
                    for entry, (original, step_id, old_call, deps, request_id)
                    in zip(steps, original_step_fields, strict=True)
                )
                and (
                    call.tool, call.capability, call.scope,
                ) == original_call[:3]
                and call.arguments is original_call[3]
                and call.request_id == original_call[4]
                and (
                    token.token_id, token.request_id, token.expires_at_ms,
                ) == original_token
                and (
                    bound.registry_revision, bound.bound_action_id,
                ) == bound_epoch[:2]
                and bound.registration is bound_epoch[2]
                and bound.call is bound_epoch[3]
            )

        try:
            before = local_stable()
            rebound = registry.bind(call)
            after = local_stable()
            stable = before and after and (
                rebound.registry_revision == bound_epoch[0]
                and rebound.bound_action_id == bound_epoch[1]
                and rebound.registration is bound_epoch[2]
                and rebound.call is bound_epoch[3]
            )
        except (AttributeError, TypeError, ValueError, KeyError) as exc:
            raise SyntheticMockCycleRejected(
                "synthetic mock input identity changed between phases"
            ) from exc
        if not stable:
            raise SyntheticMockCycleRejected(
                "synthetic mock input identity changed between phases"
            )

    assert_identity_epoch()
    if bound.registration.effect is not Effect.WRITE:
        raise SyntheticMockCycleRejected("only synthetic WRITE may enter a mock cycle")
    graph = PlanGraph(journal._steps)
    if step_id not in graph.steps or graph.steps[step_id].call.request_id != call.request_id:
        raise SyntheticMockCycleRejected("plan step is not bound to the request")
    if token.request_id != call.request_id or token.expires_at_ms <= now_ms:
        raise SyntheticMockCycleRejected("synthetic one-shot does not match or expired")
    recovery = journal.recover()
    assert_identity_epoch()
    statuses = {name: (state, rev) for name, state, rev in recovery.step_statuses}
    if statuses.get(step_id) != (StepState.PENDING.value, 0):
        raise SyntheticMockCycleRejected("not PENDING: cannot retry an UNKNOWN WRITE")
    # No backend is available to this fixture. The first durable transition
    # happens before any mock marker, and cannot be rolled back across stores.
    journal.append(step_id, StepState.RUNNING, expected_revision=0, at_ms=now_ms)
    assert_identity_epoch()
    if fault_at == "after_running":
        raise SyntheticMockCrashInjected("synthetic stop after RUNNING")
    reservation = ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence_id, now_ms=now_ms,
    )
    reservation_epoch = (
        reservation.occurrence_id, reservation.registry_revision,
        reservation.bound_action_id, reservation.request_id,
        reservation.reserved_at_ms,
    )

    def assert_reservation_epoch() -> None:
        if (
            reservation.occurrence_id, reservation.registry_revision,
            reservation.bound_action_id, reservation.request_id,
            reservation.reserved_at_ms,
        ) != reservation_epoch:
            raise SyntheticMockCycleRejected(
                "synthetic reservation receipt changed between phases"
            )

    assert_identity_epoch()
    if fault_at == "after_reservation":
        raise SyntheticMockCrashInjected("synthetic stop after reservation")
    audit_event = audit.append(call, outcome="synthetic_audit_before_mock")
    if type(audit_event) is not ActionAuditEvent:
        raise SyntheticMockCycleRejected("exact synthetic audit receipt required")
    audit_epoch = (
        audit_event.event_id, audit_event.request_id, audit_event.tool,
        audit_event.capability, audit_event.scope, audit_event.arguments_sha256,
        audit_event.outcome, audit_event.occurred_at_ms,
    )

    def assert_audit_epoch() -> None:
        if (
            type(audit_event) is not ActionAuditEvent
            or (
                audit_event.event_id, audit_event.request_id, audit_event.tool,
                audit_event.capability, audit_event.scope,
                audit_event.arguments_sha256, audit_event.outcome,
                audit_event.occurred_at_ms,
            ) != audit_epoch
            or type(audit_event.event_id) is not int
            or audit_event.event_id < 1
            or (
                audit_event.request_id, audit_event.tool,
                audit_event.capability, audit_event.scope,
                audit_event.arguments_sha256, audit_event.outcome,
            ) != (
                call.request_id, call.tool, call.capability, call.scope,
                call.arguments_sha256, "synthetic_audit_before_mock",
            )
        ):
            raise SyntheticMockCycleRejected(
                "synthetic audit receipt changed between durable phases"
            )

    assert_identity_epoch()
    assert_audit_epoch()
    assert_reservation_epoch()
    if fault_at == "after_pre_action_audit":
        raise SyntheticMockCrashInjected("synthetic stop after pre-action audit")
    # This is a separately committed local link, never external proof. A
    # failure before or after it leaves RUNNING/UNKNOWN and forbids replay.
    if link_store is not None:
        link_store.link_synthetic(
            registry, call, ledger, reservation, audit, audit_event,
            at_ms=max(now_ms, audit_event.occurred_at_ms),
        )
        assert_identity_epoch()
        assert_reservation_epoch()
        assert_audit_epoch()
        if fault_at == "after_audit_link":
            raise SyntheticMockCrashInjected("synthetic stop after audit link")
    assert_identity_epoch()
    assert_reservation_epoch()
    assert_audit_epoch()
    # Synthetic marker construction is pure and local: NOT a backend call.
    marker = "mock_" + hashlib.sha256(
        ("ARK-no-action-mock-v1\0" + reservation.occurrence_id
         + "\0" + str(audit_event.event_id)).encode("utf-8")
    ).hexdigest()
    assert_audit_epoch()
    if fault_at == "after_mock_marker":
        raise SyntheticMockCrashInjected("synthetic stop after in-memory mock marker")
    journal.append(step_id, StepState.SUCCEEDED, expected_revision=1, at_ms=now_ms)
    assert_identity_epoch()
    assert_reservation_epoch()
    assert_audit_epoch()
    return SyntheticMockCycleReceipt(
        step_id, reservation.occurrence_id, audit_event.event_id, marker,
    )
