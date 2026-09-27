"""Deterministic DAG plan state with revision-guarded transitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .contracts import PlanConflictError, PlanStep, PlanStepStatus, StepState

_ALLOWED: dict[StepState, set[StepState]] = {
    StepState.PENDING: {StepState.RUNNING, StepState.BLOCKED, StepState.CANCELLED},
    StepState.RUNNING: {StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED},
    StepState.SUCCEEDED: set(),
    StepState.FAILED: set(),
    StepState.BLOCKED: set(),
    StepState.CANCELLED: set(),
}


class PlanGraph:
    def __init__(self, steps: tuple[PlanStep, ...]) -> None:
        if not steps:
            raise ValueError("plan requires at least one step")
        self.steps = {step.step_id: step for step in steps}
        if len(self.steps) != len(steps):
            raise ValueError("plan step IDs must be unique")
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

    def statuses(self) -> Mapping[str, PlanStepStatus]:
        return dict(self._status)

    def ready_steps(self) -> tuple[PlanStep, ...]:
        ready: list[PlanStep] = []
        for step_id in sorted(self.steps):
            status = self._status[step_id]
            if status.state is not StepState.PENDING:
                continue
            dependencies = [self._status[item].state for item in self.steps[step_id].depends_on]
            if all(state is StepState.SUCCEEDED for state in dependencies):
                ready.append(self.steps[step_id])
        return tuple(ready)

    def transition(
        self,
        step_id: str,
        to_state: StepState,
        *,
        expected_revision: int,
    ) -> PlanStepStatus:
        if step_id not in self._status:
            raise KeyError(step_id)
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
        updated = replace(current, state=to_state, revision=current.revision + 1)
        self._status[step_id] = updated
        if to_state is StepState.FAILED:
            self._block_descendants(step_id)
        return updated

    def _block_descendants(self, failed_step_id: str) -> None:
        changed = True
        blocked = {failed_step_id}
        while changed:
            changed = False
            for step_id, step in self.steps.items():
                status = self._status[step_id]
                if status.state is StepState.PENDING and any(
                    dependency in blocked for dependency in step.depends_on
                ):
                    self._status[step_id] = replace(
                        status,
                        state=StepState.BLOCKED,
                        revision=status.revision + 1,
                    )
                    blocked.add(step_id)
                    changed = True

    def _assert_acyclic(self) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in visiting:
                raise ValueError("plan dependency graph contains a cycle")
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in self.steps[step_id].depends_on:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in self.steps:
            visit(step_id)
