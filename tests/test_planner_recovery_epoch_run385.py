"""Restart-only Planner reviews pin source and retained history epochs.

The fixture has no ToolBackend, approval, notification or WRITE replay path.
"""

from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _journal(path: Path):
    return SyntheticPlanJournal(
        path, (PlanStep("root", ToolCall("fixture", "write", "local")),),
    )


def _seed(tmp_path: Path):
    path = tmp_path / "planner # %.sqlite"
    journal = _journal(path)
    genesis = journal.recover().tail
    later = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10,
    ).tail
    return path, journal, genesis, later


def test_unchanged_running_witness_is_diagnostic_only(tmp_path: Path):
    _path, journal, _genesis, later = _seed(tmp_path)
    review = journal.recover(retained=later)
    assert review.ambiguous_running_steps == ("root",)
    assert review.automatic_replay_authorized is False
    assert review.dispatch_authorized is False


@pytest.mark.parametrize("replacement", ["valid_older_prefix", "bool_spoof"])
def test_reflected_retained_tail_mutation_during_replay_is_denied(
    tmp_path: Path, monkeypatch, replacement: str,
):
    _path, journal, genesis, retained = _seed(tmp_path)
    original = journal._replay

    def replace_after_replay(conn):
        state = original(conn)
        if replacement == "valid_older_prefix":
            for name in (
                "topology_digest", "event_count", "event_hash",
                "status_digest", "last_at_ms",
            ):
                object.__setattr__(retained, name, getattr(genesis, name))
        else:
            object.__setattr__(retained, "event_count", True)
        return state

    monkeypatch.setattr(journal, "_replay", replace_after_replay)
    with pytest.raises(SyntheticPlanJournalRejected, match="retained"):
        journal.recover(retained=retained)


def test_equal_path_retarget_during_read_is_denied(
    tmp_path: Path, monkeypatch,
):
    path, journal, _genesis, _later = _seed(tmp_path)
    original = journal._replay

    def retarget_after_replay(conn):
        state = original(conn)
        journal._path = Path(str(path))
        assert journal._path == path and journal._path is not path
        return state

    monkeypatch.setattr(journal, "_replay", retarget_after_replay)
    with pytest.raises(SyntheticPlanJournalRejected, match="source changed"):
        journal.recover()


def test_path_retarget_before_append_commit_rolls_back(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / "planner.sqlite"
    journal = _journal(path)
    original = journal._replay

    def retarget_after_replay(conn):
        state = original(conn)
        journal._path = Path(str(path))
        return state

    monkeypatch.setattr(journal, "_replay", retarget_after_replay)
    with pytest.raises(SyntheticPlanJournalRejected, match="source changed"):
        journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert _journal(path).recover().tail.event_count == 0


def test_invalid_path_type_is_rejected_before_review(tmp_path: Path):
    _path, journal, _genesis, _later = _seed(tmp_path)
    journal._path = str(journal._path)
    with pytest.raises(SyntheticPlanJournalRejected, match="must be a Path"):
        journal.recover()
