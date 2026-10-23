"""Fault-injection-only synthetic WRITE sequence; never dispatches a tool.

The journal, reservation ledger and audit are three independent databases.
An injected stop can leave a RUNNING/UNKNOWN WRITE; callers MUST NOT retry it.
Neither an audit row nor an in-memory mock marker proves a real side effect.
No registered backend method is ever called by this module.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .audit import SQLiteActionAudit
from .contracts import Effect, OneShotAuthorization, StepState, ToolCall
from .durable_occurrence_review import SyntheticOccurrenceStore
from .planner import PlanGraph
from .planner_journal_review import SyntheticPlanJournal
from .registry import ToolRegistry

_MAX = 2**63 - 1
_FAULTS = frozenset((
    "after_running", "after_reservation", "after_pre_action_audit",
    "after_mock_marker",
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
    ):
        raise SyntheticMockCycleRejected("exact synthetic mock inputs required")
    bound = registry.bind(call)
    if bound.registration.effect is not Effect.WRITE:
        raise SyntheticMockCycleRejected("only synthetic WRITE may enter a mock cycle")
    graph = PlanGraph(journal._steps)
    if step_id not in graph.steps or graph.steps[step_id].call.request_id != call.request_id:
        raise SyntheticMockCycleRejected("plan step is not bound to the request")
    if token.request_id != call.request_id or token.expires_at_ms <= now_ms:
        raise SyntheticMockCycleRejected("synthetic one-shot does not match or expired")
    recovery = journal.recover()
    statuses = {name: (state, rev) for name, state, rev in recovery.step_statuses}
    if statuses.get(step_id) != (StepState.PENDING.value, 0):
        raise SyntheticMockCycleRejected("not PENDING: cannot retry an UNKNOWN WRITE")
    # No backend is available to this fixture. The first durable transition
    # happens before any mock marker, and cannot be rolled back across stores.
    journal.append(step_id, StepState.RUNNING, expected_revision=0, at_ms=now_ms)
    if fault_at == "after_running":
        raise SyntheticMockCrashInjected("synthetic stop after RUNNING")
    reservation = ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence_id, now_ms=now_ms,
    )
    if fault_at == "after_reservation":
        raise SyntheticMockCrashInjected("synthetic stop after reservation")
    audit_event = audit.append(call, outcome="synthetic_audit_before_mock")
    if fault_at == "after_pre_action_audit":
        raise SyntheticMockCrashInjected("synthetic stop after pre-action audit")
    # Synthetic marker construction is pure and local: NOT a backend call.
    marker = "mock_" + hashlib.sha256(
        ("ARK-no-action-mock-v1\0" + reservation.occurrence_id
         + "\0" + str(audit_event.event_id)).encode("utf-8")
    ).hexdigest()
    if fault_at == "after_mock_marker":
        raise SyntheticMockCrashInjected("synthetic stop after in-memory mock marker")
    journal.append(step_id, StepState.SUCCEEDED, expected_revision=1, at_ms=now_ms)
    return SyntheticMockCycleReceipt(
        step_id, reservation.occurrence_id, audit_event.event_id, marker,
    )
