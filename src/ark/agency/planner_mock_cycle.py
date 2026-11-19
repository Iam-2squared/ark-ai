"""One-step composition of durable Planner state and a disconnected mock only.

The journal marks a ready step RUNNING before invoking the mock executor. Any
exception after that durable transition leaves the step ambiguous; this module
never retries it or infers rollback. Only a successful mock receipt followed
by a successful durable SUCCEEDED transition returns a cycle receipt.

This is a reversible local integration experiment, not a production dispatcher.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolRegistration,
)
from .disconnected_mock_executor import (
    DisconnectedMockExecutor,
    MockExecutionReceipt,
    MockToolBackend,
)
from .plan_registry_preflight import (
    PlanRegistryBinding,
    PlanRegistryPreflight,
    review_plan_registry_preflight,
)
from .planner import PlanGraph
from .planner_journal import (
    PlannerJournal,
    PlannerJournalReceipt,
    PlannerJournalRecovery,
    PlannerJournalTransition,
)
from .registry import ToolRegistry

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_MAX_MS = 2**63 - 1


class PlannerMockCycleRejected(RuntimeError):
    """A one-step local Planner/mock composition could not be verified."""


@dataclass(frozen=True, slots=True)
class PlannerMockCycleReceipt:
    plan_id: str
    step_id: str
    sequence_before: int
    running_sequence: int
    completed_sequence: int
    preflight_fingerprint: str
    registry_revision: str
    bound_action_id: str
    mock_receipt: MockExecutionReceipt
    journal_receipt: PlannerJournalReceipt

    @property
    def mock_only(self) -> bool:
        return True

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def exact_once_external_effect_proven(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


_RESULT_TYPE = PlannerMockCycleReceipt
_RESULT_FIELDS = (
    "plan_id", "step_id", "sequence_before", "running_sequence",
    "completed_sequence", "preflight_fingerprint", "registry_revision",
    "bound_action_id", "mock_receipt", "journal_receipt",
)
_RESULT_DENIALS = (
    "mock_only", "dispatch_authorized", "automatic_replay_authorized",
    "external_effect_proven", "exact_once_external_effect_proven",
    "trusted_clock_verified", "consent_verified",
)
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_MEMBERS = tuple(
    vars(_RESULT_TYPE).get(name)
    for name in (*_RESULT_FIELDS, *_RESULT_DENIALS, *_RESULT_HOOKS)
)

_JOURNAL_TYPE = PlannerJournal
_ORIGINAL_JOURNAL_RECOVER = vars(_JOURNAL_TYPE).get("recover")
_ORIGINAL_JOURNAL_TRANSITION = vars(_JOURNAL_TYPE).get("transition")
_EXECUTOR_TYPE = DisconnectedMockExecutor
_ORIGINAL_EXECUTOR_EXECUTE = vars(_EXECUTOR_TYPE).get("execute")
_ORIGINAL_EXECUTOR_EPOCH = vars(_EXECUTOR_TYPE).get("_assert_component_epoch")
_REGISTRY_TYPE = ToolRegistry
_ORIGINAL_REGISTRY_GET = vars(_REGISTRY_TYPE).get("get")
_PREFLIGHT_TYPE = PlanRegistryPreflight
_BINDING_TYPE = PlanRegistryBinding
_ORIGINAL_PREFLIGHT = review_plan_registry_preflight
_ORIGINAL_GRAPH_TYPE = PlanGraph
_ORIGINAL_STEP_TYPE = PlanStep
_ORIGINAL_EFFECT_TYPE = Effect
_ORIGINAL_STEP_STATE_TYPE = StepState


def _require_original_protocol() -> None:
    if (
        PlannerMockCycleReceipt is not _RESULT_TYPE
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                (*_RESULT_FIELDS, *_RESULT_DENIALS, *_RESULT_HOOKS),
                _ORIGINAL_RESULT_MEMBERS,
                strict=True,
            )
        )
        or PlannerJournal is not _JOURNAL_TYPE
        or vars(_JOURNAL_TYPE).get("recover") is not _ORIGINAL_JOURNAL_RECOVER
        or vars(_JOURNAL_TYPE).get("transition") is not _ORIGINAL_JOURNAL_TRANSITION
        or DisconnectedMockExecutor is not _EXECUTOR_TYPE
        or vars(_EXECUTOR_TYPE).get("execute") is not _ORIGINAL_EXECUTOR_EXECUTE
        or vars(_EXECUTOR_TYPE).get("_assert_component_epoch") is not _ORIGINAL_EXECUTOR_EPOCH
        or ToolRegistry is not _REGISTRY_TYPE
        or vars(_REGISTRY_TYPE).get("get") is not _ORIGINAL_REGISTRY_GET
        or PlanRegistryPreflight is not _PREFLIGHT_TYPE
        or PlanRegistryBinding is not _BINDING_TYPE
        or review_plan_registry_preflight is not _ORIGINAL_PREFLIGHT
        or PlanGraph is not _ORIGINAL_GRAPH_TYPE
        or PlanStep is not _ORIGINAL_STEP_TYPE
        or Effect is not _ORIGINAL_EFFECT_TYPE
        or StepState is not _ORIGINAL_STEP_STATE_TYPE
    ):
        raise PlannerMockCycleRejected("Planner/mock composition protocol changed")


def execute_one_mock_step(
    journal: PlannerJournal,
    plan_id: str,
    steps: tuple[PlanStep, ...],
    registry: ToolRegistry,
    executor: DisconnectedMockExecutor,
    step_id: str,
    grants: tuple[CapabilityGrant, ...],
    *,
    now_ms: int,
    one_shot: OneShotAuthorization | None = None,
    occurrence_id: str | None = None,
) -> PlannerMockCycleReceipt:
    """Persist and run exactly one currently-ready step against the exact mock.

    A failed/uncertain executor or journal operation is propagated unchanged.
    Once RUNNING is durably recorded, callers must recover the journal; this
    function never retries, marks an ambiguous step successful, or auto-replays.
    """
    _require_original_protocol()
    if (
        type(journal) is not PlannerJournal
        or type(plan_id) is not str
        or not plan_id
        or type(steps) is not tuple
        or any(type(step) is not PlanStep for step in steps)
        or type(registry) is not ToolRegistry
        or type(grants) is not tuple
        or len(grants) > 1024
        or any(type(grant) is not CapabilityGrant for grant in grants)
        or type(executor) is not DisconnectedMockExecutor
        or executor._registry is not registry
        or type(step_id) is not str
        or not step_id
        or type(now_ms) is not int
        or not 0 <= now_ms <= _MAX_MS
    ):
        raise PlannerMockCycleRejected("exact local Planner/mock inputs required")
    journal_path_epoch = journal._path
    registry_revision_epoch = registry.revision
    if type(journal_path_epoch) is not str or not journal_path_epoch:
        raise PlannerMockCycleRejected("Planner journal path identity is invalid")

    def stable() -> None:
        _require_original_protocol()
        if (
            type(journal) is not PlannerJournal
            or journal._path is not journal_path_epoch
            or type(registry) is not ToolRegistry
            or registry.revision is not registry_revision_epoch
            or type(executor) is not DisconnectedMockExecutor
            or executor._registry is not registry
        ):
            raise PlannerMockCycleRejected("Planner/mock component epoch changed")
        _ORIGINAL_EXECUTOR_EPOCH(executor)

    stable()
    recovery = _ORIGINAL_JOURNAL_RECOVER(journal, plan_id, steps)
    stable()
    if (
        type(recovery) is not PlannerJournalRecovery
        or type(recovery.graph) is not PlanGraph
        or recovery.plan_id != plan_id
        or type(recovery.sequence) is not int
        or not 0 <= recovery.sequence <= 100_000
        or type(recovery.ambiguous_running_step_ids) is not tuple
        or recovery.dispatch_authorized is not False
        or recovery.automatic_replay_authorized is not False
    ):
        raise PlannerMockCycleRejected("Planner recovery receipt is invalid")

    graph = recovery.graph
    preflight = _ORIGINAL_PREFLIGHT(graph, registry)
    stable()
    if (
        type(preflight) is not PlanRegistryPreflight
        or type(preflight.plan_topology_digest) is not str
        or type(preflight.plan_status_digest) is not str
        or type(preflight.registry_revision) is not str
        or preflight.registry_revision is not registry_revision_epoch
        or type(preflight.ready_step_ids) is not tuple
        or type(preflight.bindings) is not tuple
        or type(preflight.fingerprint) is not str
        or _SHA.fullmatch(preflight.fingerprint) is None
        or preflight.dispatch_authorized is not False
        or preflight.tool_execution_authorized is not False
        or preflight.automatic_replay_authorized is not False
        or preflight.trusted_clock_verified is not False
        or preflight.consent_verified is not False
    ):
        raise PlannerMockCycleRejected("Planner registry preflight receipt is invalid")
    if (
        preflight.plan_topology_digest != graph.topology_digest()
        or preflight.plan_status_digest != graph.status_digest()
        or any(type(item) is not PlanRegistryBinding for item in preflight.bindings)
        or any(type(item) is not str for item in preflight.ready_step_ids)
    ):
        raise PlannerMockCycleRejected("Planner registry preflight epoch changed")

    step = graph.steps.get(step_id)
    if type(step) is not PlanStep or step.step_id != step_id:
        raise PlannerMockCycleRejected("requested step is not in the recovered plan")
    if step_id not in preflight.ready_step_ids:
        raise PlannerMockCycleRejected("requested step is not currently ready")
    matches = tuple(item for item in preflight.bindings if item.step_id == step_id)
    if len(matches) != 1:
        raise PlannerMockCycleRejected("requested step has no unique registry binding")
    binding = matches[0]
    if (
        binding.tool_name != step.call.tool
        or binding.capability != step.call.capability
        or binding.request_id != step.call.request_id
        or binding.registry_revision is not registry_revision_epoch
        or type(binding.effect) is not Effect
        or type(binding.bound_action_id) is not str
        or not binding.bound_action_id
        or type(binding.backend_id) is not str
        or not binding.backend_id
    ):
        raise PlannerMockCycleRejected("requested step registry identity changed")
    registration = _ORIGINAL_REGISTRY_GET(registry, step.call.tool)
    if (
        type(registration) is not ToolRegistration
        or type(registration.backend) is not MockToolBackend
        or registration.name != binding.tool_name
        or registration.capability != binding.capability
        or registration.effect is not binding.effect
        or registration.backend_id != binding.backend_id
    ):
        raise PlannerMockCycleRejected(
            "only the exact disconnected mock backend is accepted"
        )
    if binding.effect is Effect.READ:
        if one_shot is not None or occurrence_id is not None:
            raise PlannerMockCycleRejected("READ steps cannot carry WRITE authorization inputs")
    elif binding.effect is Effect.WRITE:
        if (
            type(one_shot) is not OneShotAuthorization
            or type(occurrence_id) is not str
            or len(occurrence_id) != 68
            or _OCCURRENCE.fullmatch(occurrence_id) is None
        ):
            raise PlannerMockCycleRejected(
                "WRITE steps require exact one-shot and occurrence inputs"
            )
    else:
        raise PlannerMockCycleRejected("registered step effect is unsupported")

    status = graph.statuses().get(step_id)
    if (
        status is None
        or status.state is not StepState.PENDING
        or type(status.revision) is not int
        or not 0 <= status.revision < _MAX_MS
    ):
        raise PlannerMockCycleRejected("requested step is not in a pending state")

    stable()
    running = _ORIGINAL_JOURNAL_TRANSITION(
        journal,
        plan_id,
        graph,
        step_id,
        StepState.RUNNING,
        expected_revision=status.revision,
        expected_sequence=recovery.sequence,
    )
    stable()
    if (
        type(running) is not PlannerJournalTransition
        or type(running.receipt) is not PlannerJournalReceipt
        or running.receipt.plan_id != plan_id
        or running.receipt.sequence != recovery.sequence + 1
        or running.receipt.step_id != step_id
        or running.receipt.from_state != StepState.PENDING.value
        or running.receipt.to_state != StepState.RUNNING.value
        or running.graph.statuses()[step_id].state is not StepState.RUNNING
        or running.dispatch_authorized is not False
        or running.automatic_replay_authorized is not False
    ):
        raise PlannerMockCycleRejected("durable RUNNING transition receipt is invalid")

    # Any exception from this point leaves the durable step RUNNING. That is
    # intentional: the executor spans separate local stores and cannot prove
    # a cross-store exactly-once outcome. The caller must recover/manual-triage.
    mock = _ORIGINAL_EXECUTOR_EXECUTE(
        executor,
        step.call,
        grants,
        now_ms=now_ms,
        one_shot=one_shot,
        occurrence_id=occurrence_id,
    )
    stable()
    if (
        type(mock) is not MockExecutionReceipt
        or mock.request_id != binding.request_id
        or mock.registry_revision != binding.registry_revision
        or mock.bound_action_id != binding.bound_action_id
        or mock.effect is not binding.effect
        or mock.occurrence_id != occurrence_id
        or mock.dispatch_authorized is not False
        or mock.automatic_replay_authorized is not False
        or mock.external_effect_proven is not False
        or mock.exact_once_external_effect_proven is not False
        or mock.trusted_clock_verified is not False
        or mock.independent_custody_proven is not False
    ):
        raise PlannerMockCycleRejected("mock execution receipt does not match preflight")

    completed = _ORIGINAL_JOURNAL_TRANSITION(
        journal,
        plan_id,
        running.graph,
        step_id,
        StepState.SUCCEEDED,
        expected_revision=status.revision + 1,
        expected_sequence=running.receipt.sequence,
    )
    stable()
    if (
        type(completed) is not PlannerJournalTransition
        or type(completed.receipt) is not PlannerJournalReceipt
        or completed.receipt.plan_id != plan_id
        or completed.receipt.sequence != running.receipt.sequence + 1
        or completed.receipt.step_id != step_id
        or completed.receipt.from_state != StepState.RUNNING.value
        or completed.receipt.to_state != StepState.SUCCEEDED.value
        or completed.graph.statuses()[step_id].state is not StepState.SUCCEEDED
        or completed.graph.statuses()[step_id].revision != status.revision + 2
        or completed.dispatch_authorized is not False
        or completed.automatic_replay_authorized is not False
    ):
        raise PlannerMockCycleRejected("durable SUCCEEDED transition receipt is invalid")

    output = _RESULT_TYPE(
        plan_id=plan_id,
        step_id=step_id,
        sequence_before=recovery.sequence,
        running_sequence=running.receipt.sequence,
        completed_sequence=completed.receipt.sequence,
        preflight_fingerprint=preflight.fingerprint,
        registry_revision=binding.registry_revision,
        bound_action_id=binding.bound_action_id,
        mock_receipt=mock,
        journal_receipt=completed.receipt,
    )
    stable()
    if (
        type(output) is not PlannerMockCycleReceipt
        or output.mock_only is not True
        or output.dispatch_authorized is not False
        or output.automatic_replay_authorized is not False
        or output.external_effect_proven is not False
        or output.exact_once_external_effect_proven is not False
        or output.trusted_clock_verified is not False
        or output.consent_verified is not False
    ):
        raise PlannerMockCycleRejected("Planner/mock cycle result acquired authority")
    return output


__all__ = [
    "PlannerMockCycleReceipt",
    "PlannerMockCycleRejected",
    "execute_one_mock_step",
]
