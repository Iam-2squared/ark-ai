"""Original-carrier custody across disconnected synthetic WRITE recovery.

These tests never execute a registered backend or grant retry/authorization.
ToolCall request_id and arguments_sha256 are recomputed VALUE identities; the
actual caller-owned strings and retained witness fields are pinned by object.
"""

import pytest

import ark.agency.synthetic_recovery_triage as triage
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("recovery diagnosis must never dispatch")


def _fixture(tmp_path):
    call = ToolCall("writer", "offline.write", "local.scope", {"index": 1})
    plan = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("alpha", call),),
    )
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 25)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    return plan, ledger, audit, registry, call, backend


def _clone(text):
    copied = ("!" + text)[1:]
    assert copied == text and copied is not text
    return copied


@pytest.mark.parametrize("target", (
    "tool", "capability", "scope", "step_id", "retained_tail_digest",
))
def test_plan_graph_callback_cannot_swap_equal_original_carriers(
    tmp_path, monkeypatch, target,
):
    plan, ledger, audit, registry, call, backend = _fixture(tmp_path)
    retained = plan.recover().tail
    native_graph = triage.PlanGraph
    injections = []

    def graph_with_equal_carrier_substitution(steps):
        graph = native_graph(steps)
        if target in {"tool", "capability", "scope"}:
            object.__setattr__(
                call, target, _clone(getattr(call, target)),
            )
        elif target == "step_id":
            step = plan._steps[0]
            object.__setattr__(step, "step_id", _clone(step.step_id))
        else:
            object.__setattr__(
                retained, "status_digest", _clone(retained.status_digest),
            )
        injections.append(target)
        return graph

    monkeypatch.setattr(triage, "PlanGraph", graph_with_equal_carrier_substitution)
    with pytest.raises(
        triage.SyntheticRecoveryRejected,
        match="input, retained witness or source changed",
    ):
        triage.review_synthetic_write_recovery(
            plan, ledger, audit, registry, call,
            step_id="alpha", retained_plan=retained,
        )
    assert injections == [target]
    assert backend.calls == 0


def test_unmodified_pending_write_has_no_execution_authority(tmp_path):
    plan, ledger, audit, registry, call, backend = _fixture(tmp_path)
    retained = plan.recover().tail
    result = triage.review_synthetic_write_recovery(
        plan, ledger, audit, registry, call,
        step_id="alpha", retained_plan=retained,
    )
    assert result.step_state == "pending"
    assert result.matching_occurrences == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert backend.calls == 0
