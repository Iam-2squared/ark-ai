"""Run1407: PlannerJournal distinguishes absent class hooks from explicit None."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.agency.planner_journal as journal_module
from ark.agency.planner_journal import PlannerJournal, PlannerJournalPathError

_HOOKS = ("__getattribute__", "__getattr__")


def _journal(tmp_path: Path) -> PlannerJournal:
    return PlannerJournal(tmp_path / "planner-hook-absence.sqlite3")


def _set_class_attribute(
    carrier: type,
    name: str,
    value: object,
) -> tuple[bool, object | None]:
    namespace = vars(carrier)
    was_present = name in namespace
    original = namespace.get(name)
    type.__setattr__(carrier, name, value)
    return was_present, original


def _restore_class_attribute(
    carrier: type,
    name: str,
    original: tuple[bool, object | None],
) -> None:
    was_present, value = original
    if was_present:
        type.__setattr__(carrier, name, value)
    else:
        type.__delattr__(carrier, name)


@pytest.mark.parametrize("hook", _HOOKS)
def test_explicit_none_is_not_confused_with_an_absent_planner_journal_hook(
    tmp_path: Path,
    hook: str,
) -> None:
    journal = _journal(tmp_path)
    original = _set_class_attribute(PlannerJournal, hook, None)
    try:
        with pytest.raises(
            PlannerJournalPathError,
            match="implementation changed",
        ):
            journal_module._require_planner_journal_path_epoch(journal)
    finally:
        _restore_class_attribute(PlannerJournal, hook, original)


def test_exact_absence_sentinel_installed_as_a_hook_is_rejected(
    tmp_path: Path,
) -> None:
    journal = _journal(tmp_path)
    original = _set_class_attribute(
        PlannerJournal,
        "__getattr__",
        journal_module._PLANNER_JOURNAL_HOOK_ABSENT,
    )
    try:
        with pytest.raises(
            PlannerJournalPathError,
            match="implementation changed",
        ):
            journal_module._require_planner_journal_path_epoch(journal)
    finally:
        _restore_class_attribute(PlannerJournal, "__getattr__", original)


def test_replaced_hook_absence_sentinel_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal = _journal(tmp_path)
    monkeypatch.setattr(
        journal_module,
        "_PLANNER_JOURNAL_HOOK_ABSENT",
        object(),
    )
    with pytest.raises(
        PlannerJournalPathError,
        match="implementation changed",
    ):
        journal_module._require_planner_journal_path_epoch(journal)


def test_equal_valued_hook_name_vector_replacement_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal = _journal(tmp_path)
    replacement = tuple(list(journal_module._PLANNER_JOURNAL_HOOK_NAMES))
    assert replacement == journal_module._PLANNER_JOURNAL_HOOK_NAMES
    assert replacement is not journal_module._PLANNER_JOURNAL_HOOK_NAMES

    monkeypatch.setattr(
        journal_module,
        "_PLANNER_JOURNAL_HOOK_NAMES",
        replacement,
    )
    with pytest.raises(
        PlannerJournalPathError,
        match="implementation changed",
    ):
        journal_module._require_planner_journal_path_epoch(journal)


@pytest.mark.parametrize("hook", _HOOKS)
def test_hostile_lookup_hook_is_rejected_before_instance_lookup(
    tmp_path: Path,
    hook: str,
) -> None:
    journal = _journal(tmp_path)
    invoked: list[str] = []

    def forbidden(_self: object, _name: str) -> object:
        invoked.append(hook)
        raise AssertionError("substituted PlannerJournal lookup hook executed")

    original = _set_class_attribute(PlannerJournal, hook, forbidden)
    try:
        with pytest.raises(
            PlannerJournalPathError,
            match="implementation changed",
        ):
            journal_module._require_planner_journal_path_epoch(journal)
    finally:
        _restore_class_attribute(PlannerJournal, hook, original)

    assert invoked == []


def test_original_planner_journal_lookup_policy_remains_valid(
    tmp_path: Path,
) -> None:
    journal = _journal(tmp_path)

    assert journal_module._require_planner_journal_path_epoch(journal) == (
        object.__getattribute__(journal, "_path")
    )
