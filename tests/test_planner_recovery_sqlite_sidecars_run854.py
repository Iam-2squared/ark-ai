"""Planner SQLite path/sidecar admission remains fail-closed on restart.

Disposable local files only. No real backend, external side effect or replay
authority is granted by a healthy synthetic journal.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency import planner_journal_review as planner
from ark.agency.contracts import PlanStep, StepState, ToolCall

STEPS = (
    PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),
)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("operation", ("recover", "append", "open"))
def test_unsafe_sqlite_sidecar_denied_before_connect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, suffix: str, operation: str,
) -> None:
    path = tmp_path / "planner.sqlite"
    journal = planner.SyntheticPlanJournal(path, STEPS)
    sidecar = path.with_name(path.name + suffix)
    sidecar.mkdir()

    attempted = []

    def forbidden_connect(*_args, **_kwargs):
        attempted.append("SQLite connection")
        pytest.fail("unsafe sidecar reached sqlite3.connect")

    with monkeypatch.context() as patch:
        patch.setattr(planner.sqlite3, "connect", forbidden_connect)
        with pytest.raises(planner.SyntheticPlanJournalRejected, match="sidecar"):
            if operation == "recover":
                journal.recover()
            elif operation == "append":
                journal.append(
                    "root", StepState.RUNNING, expected_revision=0, at_ms=10,
                )
            else:
                planner.SyntheticPlanJournal(path, STEPS)
    assert attempted == []
    sidecar.rmdir()
    fresh = journal.recover()
    assert fresh.tail.event_count == 0
    assert fresh.dispatch_authorized is False
    assert fresh.automatic_replay_authorized is False


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("alias", ("hardlink", "symlink"))
def test_aliasing_sqlite_sidecar_cannot_be_admitted(
    tmp_path: Path, suffix: str, alias: str,
) -> None:
    path = tmp_path / "planner.sqlite"
    journal = planner.SyntheticPlanJournal(path, STEPS)
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"synthetic-file")
    sidecar = path.with_name(path.name + suffix)
    try:
        if alias == "hardlink":
            os.link(foreign, sidecar)
        else:
            sidecar.symlink_to(foreign)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem alias unavailable: {exc}")
    with pytest.raises(planner.SyntheticPlanJournalRejected, match="sidecar"):
        journal.recover()
    with pytest.raises(planner.SyntheticPlanJournalRejected, match="sidecar"):
        journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert foreign.read_bytes() == b"synthetic-file"


def test_orphaned_sidecar_prevents_implicit_creation(tmp_path: Path) -> None:
    path = tmp_path / "planner.sqlite"
    sidecar = path.with_name(path.name + "-wal")
    sidecar.write_bytes(b"disposable-orphan")
    with pytest.raises(planner.SyntheticPlanJournalRejected, match="sidecar"):
        planner.SyntheticPlanJournal(path, STEPS)
    assert not path.exists()
    assert sidecar.read_bytes() == b"disposable-orphan"


def test_recover_rejects_post_initialization_main_symlink_before_connect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "planner.sqlite"
    journal = planner.SyntheticPlanJournal(path, STEPS)
    moved = tmp_path / "renamed-original.sqlite"
    path.rename(moved)
    try:
        path.symlink_to(moved)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    attempted = []

    def forbidden_connect(*_args, **_kwargs):
        attempted.append("sqlite3.connect")
        pytest.fail("recovery followed redirected main SQLite path")

    with monkeypatch.context() as patch:
        patch.setattr(planner.sqlite3, "connect", forbidden_connect)
        with pytest.raises(planner.SyntheticPlanJournalRejected, match="symlink"):
            journal.recover()
    assert attempted == []


def test_oversized_journal_path_rejected_before_os_stat(tmp_path: Path) -> None:
    path = tmp_path / ("x" * 4100)
    with pytest.raises(
        planner.SyntheticPlanJournalRejected,
        match="absolute non-traversing",
    ):
        planner.SyntheticPlanJournal(path, STEPS)
    assert list(tmp_path.iterdir()) == []
