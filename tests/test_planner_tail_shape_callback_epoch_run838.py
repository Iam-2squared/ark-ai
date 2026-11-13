"""Retained Planner witness shape validation must use its original method.

Only a disposable synthetic Planner SQLite journal; no real tool dispatch,
automatic replay, permission grant, trusted clock or hardware is involved.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import planner_journal_review as planner
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _fixture(tmp_path):
    path = tmp_path / "synthetic-planner.sqlite"
    journal = planner.SyntheticPlanJournal(
        path,
        (PlanStep("root", ToolCall("mock", "read", "local", {"x": 1})),),
    )
    tail = journal.recover().tail
    return journal, path, tail


def _operation(journal, tail, operation):
    if operation == "recover":
        return journal.recover(retained=tail)
    return journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10,
        retained=tail,
    )


@pytest.mark.parametrize("operation", ("recover", "append"))
def test_preinstalled_retained_shape_method_never_executes(
    tmp_path, monkeypatch, operation,
):
    journal, path, tail = _fixture(tmp_path)
    called = []

    def poison(_self):
        called.append("shape")
        raise AssertionError("substituted retained-shape validation executed")

    def forbid_path():
        called.append("path")
        raise AssertionError("journal filesystem opened with altered witness method")

    with monkeypatch.context() as patch:
        patch.setattr(planner.SyntheticPlanTail, "assert_shape", poison)
        patch.setattr(journal, "_assert_source_path", forbid_path)
        with pytest.raises(
            planner.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            _operation(journal, tail, operation)
    assert called == []
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone() == (0,)


@pytest.mark.parametrize("operation", ("recover", "append"))
def test_topology_callback_cannot_swap_retained_shape_method(
    tmp_path, monkeypatch, operation,
):
    journal, path, tail = _fixture(tmp_path)
    touched = []
    original_pin = journal._pin_topology

    def poison(_self):
        touched.append("shape")
        raise AssertionError("late substituted retained-shape method executed")

    with monkeypatch.context() as patch:
        def swap_after_topology():
            original = original_pin()
            patch.setattr(planner.SyntheticPlanTail, "assert_shape", poison)
            return original

        patch.setattr(journal, "_pin_topology", swap_after_topology)
        with pytest.raises(
            planner.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            _operation(journal, tail, operation)
    assert touched == []
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone() == (0,)


def test_valid_retained_tail_still_supports_local_recovery_and_cas(tmp_path):
    journal, _path, retained = _fixture(tmp_path)
    preview = journal.recover(retained=retained)
    assert preview.tail.event_count == 0
    assert preview.dispatch_authorized is False
    committed = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10,
        retained=retained,
    )
    restarted = journal.recover(retained=committed.tail)
    assert restarted.ambiguous_running_steps == ("root",)
    assert restarted.automatic_replay_authorized is False
    assert restarted.dispatch_authorized is False
