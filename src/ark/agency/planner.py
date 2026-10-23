"""Deterministic DAG plan state with revision-guarded transitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType

from .contracts import PlanConflictError, PlanStep, PlanStepStatus, StepState

_ALLOWED: Mapping[StepState, frozenset[StepState]] = MappingProxyType(
    {
        StepState.PENDING: frozenset(
            {StepState.RUNNING, StepState.BLOCKED, StepState.CANCELLED}
        ),
        StepState.RUNNING: frozenset(
            {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED}
        ),
        StepState.SUCCEEDED: frozenset(),
        StepState.FAILED: frozenset(),
        StepState.BLOCKED: frozenset(),
        StepState.CANCELLED: frozenset(),
    }
)


class PlanGraph:
    def __init__(self, steps: tuple[PlanStep, ...]) -> None:
        if type(steps) is not tuple or any(type(step) is not PlanStep for step in steps):
            raise TypeError("steps must be a tuple of exact PlanStep values")
        if not steps:
            raise ValueError("plan requires at least one step")
        step_map = {step.step_id: step for step in steps}
        if len(step_map) != len(steps):
            raise ValueError("plan step IDs must be unique")
        self.steps: Mapping[str, PlanStep] = MappingProxyType(step_map)
        for step in steps:
            unknown = set(step.depends_on) - self.steps.keys()
            if unknown:
                raise ValueError(f"unknown dependency for {step.step_id}: {sorted(unknown)}")
            if step.step_id in step.depends_on:
                raise ValueError("step may not depend on itself")
        self._assert_acyclic()
        self._status = {
            step.step_id: PlanStepStatus(step.step_id, StepState.PENDING, 0)
            for step in steps
        }
        # A MappingProxyType protects the mapping, not its frozen dataclass
        # values against object.__setattr__ reflection. Pin exact plan inputs.
        self._step_mapping_epoch = self.steps
        self._step_epoch = tuple(
            (step_id, step, step.call, step.depends_on, step.call.arguments, step.call.request_id)
            for step_id, step in sorted(self.steps.items())
        )

    def _assert_plan_epoch(self) -> None:
        if (
            type(self.steps) is not MappingProxyType
            or self.steps is not self._step_mapping_epoch
            or type(self._step_epoch) is not tuple
            or len(self._step_epoch) != len(self.steps)
        ):
            raise PlanConflictError("plan mapping changed after construction")
        for step_id, step, call, depends_on, arguments, request_id in self._step_epoch:
            if (
                type(step) is not PlanStep
                or type(step.step_id) is not str
                or step.step_id != step_id
                or self.steps.get(step_id) is not step
                or step.call is not call
                or type(call) is not type(step.call)
                or type(depends_on) is not tuple
                or step.depends_on is not depends_on
                or call.arguments is not arguments
            ):
                raise PlanConflictError("plan step input changed after construction")
            try:
                current_request_id = call.request_id
            except (TypeError, ValueError, AttributeError) as exc:
                raise PlanConflictError("plan action input is invalid") from exc
            if current_request_id != request_id:
                raise PlanConflictError("plan action identity changed after construction")

    def statuses(self) -> Mapping[str, PlanStepStatus]:
        self._assert_plan_epoch()
        # Return detached value snapshots: frozen dataclass fields can still be
        # changed by object.__setattr__ on a caller-held reference.
        return MappingProxyType({key: replace(value) for key, value in self._status.items()})

    def ready_steps(self) -> tuple[PlanStep, ...]:
        self._assert_plan_epoch()
        ready: list[PlanStep] = []
        for step_id in sorted(self.steps):
            status = self._status[step_id]
            if status.state is not StepState.PENDING:
                continue
            dependencies = [self._status[item].state for item in self.steps[step_id].depends_on]
            if all(state is StepState.SUCCEEDED for state in dependencies):
                ready.append(self.steps[step_id])
        self._assert_plan_epoch()
        return tuple(ready)

    def transition(
        self,
        step_id: str,
        to_state: StepState,
        *,
        expected_revision: int,
    ) -> PlanStepStatus:
        self._assert_plan_epoch()
        if type(step_id) is not str or not step_id.strip():
            raise TypeError("step_id must be a non-empty exact string")
        if step_id not in self._status:
            raise KeyError(step_id)
        if type(to_state) is not StepState:
            raise TypeError("to_state must be an exact StepState")
        if (
            type(expected_revision) is not int
            or not 0 <= expected_revision <= 2**63 - 1
        ):
            raise ValueError(
                "expected_revision must be a non-negative exact integer "
                "within SQLite range"
            )
        current = self._status[step_id]
        if expected_revision != current.revision:
            raise PlanConflictError(
                f"revision mismatch: expected {expected_revision}, actual {current.revision}"
            )
        if to_state not in _ALLOWED[current.state]:
            raise PlanConflictError(
                f"invalid transition: {current.state.value} -> {to_state.value}"
            )
        if to_state is StepState.RUNNING:
            dependency_states = [
                self._status[item].state for item in self.steps[step_id].depends_on
            ]
            if not all(state is StepState.SUCCEEDED for state in dependency_states):
                raise PlanConflictError("step dependencies are not satisfied")
        if current.revision == 2**63 - 1:
            raise PlanConflictError("plan revision exhausted SQLite INTEGER range")
        # A cascading BLOCKED revision can overflow independently of the
        # explicitly transitioned step. Check *all* affected descendants
        # before publishing any state change; never leave half a cascade.
        descendants: tuple[str, ...] = ()
        if to_state in {
            StepState.FAILED,
            StepState.CANCELLED,
            StepState.BLOCKED,
        }:
            descendants = self._pending_descendants(step_id)
            if any(
                type(self._status[item].revision) is not int
                or not 0 <= self._status[item].revision < 2**63 - 1
                for item in descendants
            ):
                raise PlanConflictError("dependent revision exhausted SQLite INTEGER range")

        updated = replace(current, state=to_state, revision=current.revision + 1)
        self._status[step_id] = updated
        for item in descendants:
            status = self._status[item]
            self._status[item] = replace(
                status, state=StepState.BLOCKED, revision=status.revision + 1
            )
        # Never expose the in-map status value to callers.
        return replace(updated)

    def _pending_descendants(self, failed_step_id: str) -> tuple[str, ...]:
        """Preflight pending descendants in O(steps + edges), without mutation.

        A non-PENDING barrier cannot be traversed. Collection before mutation
        ensures an overflowing downstream revision cannot partially block a DAG.
        """
        dependents: dict[str, list[str]] = {step_id: [] for step_id in self.steps}
        for step_id, step in self.steps.items():
            for dependency in step.depends_on:
                dependents[dependency].append(step_id)

        pending = [failed_step_id]
        seen = {failed_step_id}
        descendants: list[str] = []
        while pending:
            parent = pending.pop()
            for child in dependents[parent]:
                if child in seen:
                    continue
                seen.add(child)
                if self._status[child].state is not StepState.PENDING:
                    continue
                descendants.append(child)
                pending.append(child)
        return tuple(descendants)

    def _assert_acyclic(self) -> None:
        """Validate arbitrarily deep DAGs without Python recursion exhaustion."""
        active: set[str] = set()
        complete: set[str] = set()
        for root in sorted(self.steps):
            if root in complete:
                continue
            # Exit markers faithfully model recursive DFS while keeping memory
            # usage bounded by the graph depth rather than the call-stack limit.
            stack: list[tuple[str, bool]] = [(root, False)]
            while stack:
                step_id, finish = stack.pop()
                if finish:
                    active.remove(step_id)
                    complete.add(step_id)
                    continue
                if step_id in complete:
                    continue
                if step_id in active:
                    raise ValueError("plan dependency graph contains a cycle")
                active.add(step_id)
                stack.append((step_id, True))
                stack.extend(
                    (dependency, False)
                    for dependency in reversed(self.steps[step_id].depends_on)
                    if dependency not in complete
                )
