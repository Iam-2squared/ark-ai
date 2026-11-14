"""Every synthetic crash prefix remains UNKNOWN through a mixed-DAG restart.

Four disposable SQLite files commit independently. A mock success marker is
not a backend outcome, issuer approval, or authority to replay any WRITE.
"""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("disconnected crash/restart fixture must not dispatch")


def _state(root):
    root.mkdir(parents=True, exist_ok=True)
    calls = {
        "root": ToolCall("writer", "offline.write", "fixture", {"step": "root"}),
        "dependent": ToolCall(
            "writer", "offline.write", "fixture", {"step": "dependent"},
        ),
        "independent": ToolCall(
            "writer", "offline.write", "fixture", {"step": "independent"},
        ),
    }
    bridge = ToolCall("reader", "offline.read", "fixture")
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("root", calls["root"]),
        PlanStep("bridge", bridge, ("root",)),
        PlanStep("dependent", calls["dependent"], ("bridge",)),
        PlanStep("independent", calls["independent"]),
    ))
    ledger = SyntheticOccurrenceStore(root / "occurrence.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
        ToolRegistration("reader", "offline.read", Effect.READ, "mock", backend),
    ))
    return journal, ledger, audit, links, registry, calls, backend


def _run(state, name, *, now_ms=10, fault=None):
    journal, ledger, audit, links, registry, calls, _backend = state
    call = calls[name]
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call,
        OneShotAuthorization("token-" + name, call.request_id, 1000),
        step_id=name,
        occurrence_id="occ_" + ("a" if name == "root" else "b") * 64,
        now_ms=now_ms, fault_at=fault, link_store=links,
    )


def _review(state, **retained):
    journal, ledger, audit, links, registry, _calls, backend = state
    outcome = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=links, **retained,
    )
    assert backend.calls == 0
    assert outcome.dispatch_authorized is False
    assert outcome.automatic_replay_authorized is False
    assert outcome.external_outcome_known is False
    return outcome


@pytest.mark.parametrize("fault", (
    "after_running",
    "after_reservation",
    "after_pre_action_audit",
    "after_audit_link",
    "after_mock_marker",
))
def test_each_mixed_write_crash_prefix_survives_reopen_without_replay(
    tmp_path, fault,
):
    initial = _state(tmp_path)
    with pytest.raises(SyntheticMockCrashInjected, match="synthetic stop"):
        _run(initial, "root", fault=fault)
    # Another independent mock WRITE may complete without resolving the root.
    independent = _run(initial, "independent", now_ms=12)
    assert not independent.external_outcome_known

    before = _review(initial)
    assert before.uncertain_step_ids == ("independent", "root")
    assert before.downstream_write_hold_step_ids == ("dependent",)
    first = before.steps[0]
    retained = dict(
        retained_plan=first.plan_tail,
        retained_ledger=first.ledger_witness,
        retained_audit=first.audit_witness,
        retained_link=first.link_witness,
    )
    assert first.link_witness.event_count == (
        2 if fault in {"after_audit_link", "after_mock_marker"} else 1
    )
    assert initial[1].count_synthetic() == (
        1 if fault == "after_running" else 2
    )
    assert len(initial[2].events()) == (
        1 if fault in {"after_running", "after_reservation"} else 2
    )
    assert initial[6].calls == 0

    reopened = _state(tmp_path)
    assert _review(reopened, **retained) == before
    assert reopened[0].recover().ambiguous_running_steps == ("root",)
    for name in ("root", "independent"):
        with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
            _run(reopened, name, now_ms=20)
    assert reopened[1].count_synthetic() == initial[1].count_synthetic()
    assert reopened[6].calls == 0
