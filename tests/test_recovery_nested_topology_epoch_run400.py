"""Disconnected recovery pins individual PlanStep inputs before callbacks.

A stable journal tuple cannot attest its reflected-mutable nested steps.
No test dispatches a ToolBackend or resolves UNKNOWN external WRITE.
"""

from pathlib import Path
from types import MappingProxyType

import pytest

import ark.agency.synthetic_recovery_triage as recovery
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("a recovery review cannot dispatch tools")


def _fixture(tmp_path: Path):
    initial = ToolCall("offline", "mock", "local", {"stage": 0})
    target = ToolCall("offline", "mock", "local", {"stage": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite",
        (PlanStep("initial", initial),
         PlanStep("target", target, depends_on=("initial",))),
    )
    path = tmp_path / "reservations.sqlite"
    SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = ToolRegistry((
        ToolRegistration("offline", "mock", Effect.WRITE, "mock", NeverBackend()),
    ))
    return journal, path, audit, registry, target


def _review(state):
    journal, path, audit, registry, target = state
    return recovery.review_synthetic_write_recovery(
        journal, path, audit, registry, target, step_id="target",
    )


def test_stable_nested_topology_still_inert(tmp_path):
    result = _review(_fixture(tmp_path))
    assert result.step_state == "pending"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False


@pytest.mark.parametrize("change", ("step_id", "step_call", "deps", "arguments"))
def test_first_bind_cannot_rebase_nested_step_epoch(
    tmp_path, monkeypatch, change,
):
    state = _fixture(tmp_path)
    step = state[0]._steps[1]
    original_bind = ToolRegistry.bind

    def bind(self, call):
        bound = original_bind(self, call)
        if change == "step_id":
            object.__setattr__(step, "step_id", "another")
        elif change == "step_call":
            replacement = ToolCall(
                step.call.tool, step.call.capability, step.call.scope,
                dict(step.call.arguments),
            )
            assert replacement is not step.call
            object.__setattr__(step, "call", replacement)
        elif change == "deps":
            replacement = tuple(list(step.depends_on))
            assert replacement == step.depends_on
            assert replacement is not step.depends_on
            object.__setattr__(step, "depends_on", replacement)
        else:
            old_arguments = step.call.arguments
            replacement = MappingProxyType(dict(old_arguments))
            assert replacement is not old_arguments
            object.__setattr__(step.call, "arguments", replacement)
        return bound

    monkeypatch.setattr(ToolRegistry, "bind", bind)
    with pytest.raises(recovery.SyntheticRecoveryRejected, match="input"):
        _review(state)


def test_graph_constructor_cannot_rebase_nested_dependencies(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    step = state[0]._steps[1]
    original_graph = recovery.PlanGraph

    def graph(steps):
        result = original_graph(steps)
        object.__setattr__(step, "depends_on", tuple(list(step.depends_on)))
        return result

    monkeypatch.setattr(recovery, "PlanGraph", graph)
    with pytest.raises(recovery.SyntheticRecoveryRejected, match="input"):
        _review(state)
