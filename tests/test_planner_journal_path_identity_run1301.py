"""Run1301: production PlannerJournal path identity is immutable and pre-I/O checked."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import ark.agency.planner_journal as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import PlannerJournal, PlannerJournalPathError


_PLAN_ID = "planner-path-identity-run1301"


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep(
            "root",
            ToolCall("fixture.root", "fixture.read", "synthetic:private", {"value": "root"}),
        ),
    )


def _journal(tmp_path: Path) -> PlannerJournal:
    journal = PlannerJournal(tmp_path / "planner.sqlite3")
    journal.create_plan(_PLAN_ID, PlanGraph(_steps()))
    return journal


def _deny_sqlite(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    calls: list[object] = []

    def forbidden_connect(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("retargeted PlannerJournal must be denied before SQLite")

    monkeypatch.setattr(journal_module.sqlite3, "connect", forbidden_connect)
    return calls


def test_path_slots_refuse_ordinary_assignment_and_deletion(tmp_path: Path) -> None:
    journal = _journal(tmp_path)

    for name in ("_path", "_path_identity"):
        current = object.__getattribute__(journal, name)
        with pytest.raises(AttributeError, match="path identity is immutable"):
            setattr(journal, name, current)
        with pytest.raises(AttributeError, match="path identity is immutable"):
            delattr(journal, name)

    recovered = journal.recover(_PLAN_ID, _steps())
    assert recovered.sequence == 0
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    transitioned = journal.transition(
        _PLAN_ID,
        recovered.graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    assert transitioned.receipt.sequence == 1
    assert transitioned.graph.statuses()["root"].state is StepState.RUNNING


@pytest.mark.parametrize("slot", ("_path", "_path_identity"))
@pytest.mark.parametrize("replacement", ("different", "equal_carrier"))
def test_reflective_path_retarget_is_denied_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    slot: str,
    replacement: str,
) -> None:
    journal = _journal(tmp_path)
    original = object.__getattribute__(journal, "_path")
    other = tmp_path / "redirect.sqlite3"
    candidate = (
        str(other)
        if replacement == "different"
        else original.encode("utf-8").decode("utf-8")
    )
    assert type(candidate) is str
    if replacement == "equal_carrier":
        assert candidate == original and candidate is not original
    object.__setattr__(journal, slot, candidate)

    calls = _deny_sqlite(monkeypatch)
    with pytest.raises(PlannerJournalPathError, match="source identity changed"):
        journal.recover(_PLAN_ID, _steps())

    assert calls == []
    assert not other.exists()
    assert os.path.isfile(original)


@pytest.mark.parametrize("guard", ("__setattr__", "__delattr__", "_connect"))
def test_replaced_class_path_guard_is_denied_before_sqlite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    guard: str,
) -> None:
    journal = _journal(tmp_path)
    guard_calls: list[bool] = []

    def substituted(*_args: object, **_kwargs: object) -> None:
        guard_calls.append(True)
        raise AssertionError("substituted PlannerJournal guard must not execute")

    monkeypatch.setattr(PlannerJournal, guard, substituted)
    calls = _deny_sqlite(monkeypatch)

    with pytest.raises(PlannerJournalPathError, match="implementation changed"):
        journal.recover(_PLAN_ID, _steps())

    assert guard_calls == []
    assert calls == []


def test_path_slot_shadow_in_instance_dictionary_is_denied(tmp_path: Path) -> None:
    journal = _journal(tmp_path)
    object.__getattribute__(journal, "__dict__")["_path"] = str(tmp_path / "shadow.sqlite3")

    with pytest.raises(PlannerJournalPathError, match="source identity changed"):
        journal.recover(_PLAN_ID, _steps())

    assert not (tmp_path / "shadow.sqlite3").exists()


def test_planner_journal_subclass_is_rejected_before_file_creation(tmp_path: Path) -> None:
    class DerivedPlannerJournal(PlannerJournal):
        pass

    path = tmp_path / "derived.sqlite3"
    with pytest.raises(PlannerJournalPathError, match="exact PlannerJournal type"):
        DerivedPlannerJournal(path)
    assert not path.exists()
