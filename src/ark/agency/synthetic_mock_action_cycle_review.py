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
from .durable_occurrence_review import SyntheticOccurrenceStore, SyntheticReservationReceipt
from .planner import PlanGraph
from .planner_journal_review import SyntheticPlanJournal
from .registry import BoundAction, ToolRegistry
from .synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkReceipt,
    SyntheticAuditLinkWitness,
    SyntheticOccurrenceAuditLinkStore,
)

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


_CYCLE_RECEIPT_TYPE = SyntheticMockCycleReceipt
_CYCLE_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "external_outcome_known",
)
_ORIGINAL_CYCLE_DENIALS = tuple(
    vars(_CYCLE_RECEIPT_TYPE)[name] for name in _CYCLE_DENIALS
)
_ORIGINAL_CYCLE_RECEIPT_INIT = vars(_CYCLE_RECEIPT_TYPE)["__init__"]
_CYCLE_FIELDS = ("step_id", "occurrence_id", "audit_event_id", "mock_marker")
_ORIGINAL_CYCLE_FIELDS = tuple(
    vars(_CYCLE_RECEIPT_TYPE)[name] for name in _CYCLE_FIELDS
)
_CYCLE_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_CYCLE_HOOKS = tuple(
    vars(_CYCLE_RECEIPT_TYPE).get(name) for name in _CYCLE_HOOKS
)


def _assert_original_cycle_denials() -> None:
    # Reject False-looking counterfeit descriptors without invoking them.
    # The local success marker is not real authorization or outcome proof.
    if (
        SyntheticMockCycleReceipt is not _CYCLE_RECEIPT_TYPE
        or vars(_CYCLE_RECEIPT_TYPE).get("__init__")
        is not _ORIGINAL_CYCLE_RECEIPT_INIT
        or any(
            vars(_CYCLE_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _CYCLE_FIELDS, _ORIGINAL_CYCLE_FIELDS, strict=True,
            )
        )
        or any(
            vars(_CYCLE_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _CYCLE_HOOKS, _ORIGINAL_CYCLE_HOOKS, strict=True,
            )
        )
        or any(
            vars(_CYCLE_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _CYCLE_DENIALS, _ORIGINAL_CYCLE_DENIALS, strict=True,
            )
        )
    ):
        raise SyntheticMockCycleRejected(
            "synthetic mock receipt authority descriptor changed"
        )


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
    _assert_original_cycle_denials()
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
         entry.call.request_id, entry.call.tool,
         entry.call.capability, entry.call.scope)
        for entry in original_steps
    )
    bound = registry.bind(call)
    # The binding callback must resolve this exact original ToolCall and
    # registered backend before RUNNING is durably journaled. Consistently
    # returning a forged, value-equal BoundAction must not defer rejection
    # until after an independent occurrence reservation is committed.
    if (
        type(bound) is not BoundAction
        or bound.call is not call
        or bound.registration is not registry.get(call.tool)
        or bound.registry_revision != registry.revision
    ):
        raise SyntheticMockCycleRejected(
            "synthetic mock registry binding differs from requested WRITE"
        )

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
                    and entry.step_id is step_id
                    and entry.call is old_call
                    and entry.depends_on is deps
                    and entry.call.request_id == request_id
                    and entry.call.tool is old_tool
                    and entry.call.capability is old_capability
                    and entry.call.scope is old_scope
                    for entry, (
                        original, step_id, old_call, deps, request_id,
                        old_tool, old_capability, old_scope,
                    ) in zip(steps, original_step_fields, strict=True)
                )
                and (
                    call.tool, call.capability, call.scope,
                ) == original_call[:3]
                and all(
                    new is old
                    for new, old in zip(
                        (call.tool, call.capability, call.scope),
                        original_call[:3], strict=True,
                    )
                )
                and call.arguments is original_call[3]
                and call.request_id == original_call[4]
                and (
                    token.token_id, token.request_id, token.expires_at_ms,
                ) == original_token
                and token.token_id is original_token[0]
                and token.request_id is original_token[1]
                and token.expires_at_ms is original_token[2]
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
    _assert_original_cycle_denials()
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
    # The journal append is an overridable callback, not proof of a durable
    # RUNNING state. Reopen and replay the journal before touching the separate
    # occurrence ledger: a no-op, forged receipt, or immediate terminal drift
    # must not reserve a one-shot occurrence for a step that is not RUNNING.
    running = journal.recover(retained=recovery.tail)
    assert_identity_epoch()
    running_states = {
        name: (state, revision)
        for name, state, revision in running.step_statuses
    }
    if (
        running_states.get(step_id) != (StepState.RUNNING.value, 1)
        or step_id not in running.ambiguous_running_steps
        or running.tail.event_count != recovery.tail.event_count + 1
    ):
        raise SyntheticMockCycleRejected(
            "durable RUNNING journal transition not confirmed"
        )
    if fault_at == "after_running":
        raise SyntheticMockCrashInjected("synthetic stop after RUNNING")
    reservation = ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence_id, now_ms=now_ms,
    )
    # The occurrence fixture is a separately committed store. An injected or
    # corrupt return value must never be used as a different audit subject or
    # let the journal finish SUCCEEDED. A failed check leaves RUNNING/UNKNOWN;
    # it cannot roll back the prior journal or reservation across stores.
    assert_identity_epoch()
    if (
        type(reservation) is not SyntheticReservationReceipt
        or reservation.occurrence_id != occurrence_id
        or reservation.registry_revision != bound.registry_revision
        or reservation.bound_action_id != bound.bound_action_id
        or reservation.request_id != call.request_id
        or type(reservation.reserved_at_ms) is not int
        or reservation.reserved_at_ms != now_ms
    ):
        raise SyntheticMockCycleRejected(
            "synthetic reservation receipt differs from requested WRITE"
        )
    reservation_epoch = (
        reservation.occurrence_id, reservation.registry_revision,
        reservation.bound_action_id, reservation.request_id,
        reservation.reserved_at_ms,
    )

    def assert_reservation_epoch() -> None:
        if (
            type(reservation) is not SyntheticReservationReceipt
            or any(
                current is not original
                for current, original in zip(
                    (
                        reservation.occurrence_id, reservation.registry_revision,
                        reservation.bound_action_id, reservation.request_id,
                        reservation.reserved_at_ms,
                    ), reservation_epoch, strict=True,
                )
            )
        ):
            raise SyntheticMockCycleRejected(
                "synthetic reservation receipt changed between phases"
            )

    assert_identity_epoch()
    if fault_at == "after_reservation":
        raise SyntheticMockCrashInjected("synthetic stop after reservation")
    # A post-append receipt is not proof of persistence: snapshot the
    # existing append tip first, then require precisely one NEW durable row.
    # Bounded pagination is intentional for disconnected fixtures; reject an
    # oversized history instead of silently accepting an unchecked prefix.
    def observed_audit_tip() -> int:
        last = 0
        for _ in range(41):
            page = audit.events(after_event_id=last, limit=1000)
            assert_identity_epoch()
            assert_reservation_epoch()
            if (
                type(page) is not list
                or len(page) > 1000
                or any(
                    type(event) is not ActionAuditEvent
                    or type(event.event_id) is not int
                    or event.event_id != last + index + 1
                    for index, event in enumerate(page)
                )
            ):
                raise SyntheticMockCycleRejected(
                    "synthetic audit preflight history changed"
                )
            if not page:
                return last
            last = page[-1].event_id
            if len(page) < 1000:
                return last
        raise SyntheticMockCycleRejected(
            "synthetic audit preflight history exceeds local fixture bound"
        )

    audit_prior_tip = observed_audit_tip()
    assert_identity_epoch()
    assert_reservation_epoch()
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
            or any(
                current is not original
                for current, original in zip(
                    (
                        audit_event.event_id, audit_event.request_id,
                        audit_event.tool, audit_event.capability,
                        audit_event.scope, audit_event.arguments_sha256,
                        audit_event.outcome, audit_event.occurred_at_ms,
                    ), audit_epoch, strict=True,
                )
            )
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

    def assert_durable_audit_epoch() -> None:
        # Never infer an audit-before-action boundary from an in-memory
        # append return. A no-op/forged callback or a reused old row must
        # leave the already-reserved mock WRITE UNKNOWN, not SUCCEEDED.
        persisted = audit.events(after_event_id=audit_prior_tip, limit=2)
        assert_identity_epoch()
        assert_reservation_epoch()
        assert_audit_epoch()
        if (
            type(persisted) is not list
            or len(persisted) != 1
            or type(persisted[0]) is not ActionAuditEvent
            or type(persisted[0].event_id) is not int
            or persisted[0].event_id != audit_prior_tip + 1
            or (
                persisted[0].event_id, persisted[0].request_id,
                persisted[0].tool, persisted[0].capability,
                persisted[0].scope, persisted[0].arguments_sha256,
                persisted[0].outcome, persisted[0].occurred_at_ms,
            ) != audit_epoch
        ):
            raise SyntheticMockCycleRejected(
                "durable pre-action audit transition not confirmed"
            )

    assert_identity_epoch()
    assert_audit_epoch()
    assert_reservation_epoch()
    assert_durable_audit_epoch()
    if fault_at == "after_pre_action_audit":
        raise SyntheticMockCrashInjected("synthetic stop after pre-action audit")
    # This is a separately committed local link, never external proof. A
    # failure before or after it leaves RUNNING/UNKNOWN and forbids replay.
    linked_witness = None
    if link_store is not None:
        # A link callback receipt alone is not proof that its independent
        # SQLite sidecar committed. Retain its pre-call high-water, then
        # require exactly one new, identity-bound, persisted link.
        before_link = link_store.read_witness()
        assert_identity_epoch()
        assert_reservation_epoch()
        assert_audit_epoch()
        assert_durable_audit_epoch()
        link_receipt = link_store.link_synthetic(
            registry, call, ledger, reservation, audit, audit_event,
            at_ms=max(now_ms, audit_event.occurred_at_ms),
            retained=before_link,
        )
        assert_identity_epoch()
        assert_reservation_epoch()
        assert_audit_epoch()
        if (
            type(link_receipt) is not SyntheticAuditLinkReceipt
            or link_receipt.occurrence_id != reservation.occurrence_id
            or link_receipt.audit_event_id != audit_event.event_id
            or type(link_receipt.link_hash) is not str
        ):
            raise SyntheticMockCycleRejected(
                "synthetic audit link receipt differs from requested WRITE"
            )
        linked_witness = link_store.read_witness(retained=before_link)
        assert_identity_epoch()
        assert_reservation_epoch()
        assert_audit_epoch()
        if (
            type(linked_witness) is not SyntheticAuditLinkWitness
            or linked_witness.event_count != before_link.event_count + 1
            or linked_witness.tail_hash != link_receipt.link_hash
            or linked_witness.last_link_at_ms != max(
                now_ms, audit_event.occurred_at_ms,
            )
        ):
            raise SyntheticMockCycleRejected(
                "durable synthetic audit link transition not confirmed"
            )
        if fault_at == "after_audit_link":
            raise SyntheticMockCrashInjected("synthetic stop after audit link")
    assert_identity_epoch()
    assert_reservation_epoch()
    assert_audit_epoch()
    assert_durable_audit_epoch()
    # Synthetic marker construction is pure and local: NOT a backend call.
    marker = "mock_" + hashlib.sha256(
        ("ARK-no-action-mock-v1\0" + reservation.occurrence_id
         + "\0" + str(audit_event.event_id)).encode("utf-8")
    ).hexdigest()
    assert_audit_epoch()
    if fault_at == "after_mock_marker":
        raise SyntheticMockCrashInjected("synthetic stop after in-memory mock marker")
    _assert_original_cycle_denials()
    assert_durable_audit_epoch()
    journal.append(step_id, StepState.SUCCEEDED, expected_revision=1, at_ms=now_ms)
    # An append callback and its returned receipt do not prove the terminal
    # journal row exists. Reopen the independent SQLite journal and require
    # precisely one terminal event after the retained RUNNING watermark.
    # If persistence is missing, changed, or ambiguous, keep the externally
    # unverified mock WRITE in manual-only/UNKNOWN reconciliation.
    finished = journal.recover(retained=running.tail)
    assert_identity_epoch()
    assert_reservation_epoch()
    assert_audit_epoch()
    _assert_original_cycle_denials()
    # Terminal callbacks can mutate other SQLite databases after the earlier
    # readbacks. A confirmed local SUCCEEDED row is insufficient if its
    # pre-action audit or optional sidecar linkage has since disappeared.
    assert_durable_audit_epoch()
    if link_store is not None:
        final_link = link_store.read_witness(retained=linked_witness)
        assert_identity_epoch()
        assert_reservation_epoch()
        assert_audit_epoch()
        if (
            type(final_link) is not SyntheticAuditLinkWitness
            or final_link != linked_witness
        ):
            raise SyntheticMockCycleRejected(
                "synthetic audit link changed after journal terminal"
            )
    finished_states = {
        name: (state, revision)
        for name, state, revision in finished.step_statuses
    }
    if (
        finished_states.get(step_id) != (StepState.SUCCEEDED.value, 2)
        or step_id in finished.ambiguous_running_steps
        or finished.tail.event_count != running.tail.event_count + 1
    ):
        raise SyntheticMockCycleRejected(
            "durable SUCCEEDED journal transition not confirmed"
        )
    result = _CYCLE_RECEIPT_TYPE(
        step_id, reservation.occurrence_id, audit_event.event_id, marker,
    )
    _assert_original_cycle_denials()
    if (
        type(result) is not _CYCLE_RECEIPT_TYPE
        or result.step_id is not step_id
        or result.occurrence_id is not reservation.occurrence_id
        or result.audit_event_id is not audit_event.event_id
        or result.mock_marker is not marker
        or any(getattr(result, flag) is not False for flag in _CYCLE_DENIALS)
    ):
        raise SyntheticMockCycleRejected("synthetic mock receipt changed")
    _assert_original_cycle_denials()
    return result
