"""Fail-closed Planner witness custody before and after local SQLite COMMIT.

No physical tools, external backend, authenticated user, or automatic replay.
A post-COMMIT rejection MUST preserve the durable synthetic event.
"""

from dataclasses import replace

import pytest

import ark.agency.planner_journal_review as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _journal(tmp_path):
    step = PlanStep(
        "root", ToolCall("offline", "read.mock", "local", {"fixture": True}),
    )
    return SyntheticPlanJournal(tmp_path / "planner.sqlite", (step,))


def _poison(result, mode):
    if mode == "alien_type":
        return object()
    if mode == "cloned_tail":
        object.__setattr__(result, "tail", replace(result.tail))
    elif mode == "tail_event_count":
        object.__setattr__(
            result.tail, "event_count", result.tail.event_count + 1,
        )
    elif mode == "tail_hash":
        object.__setattr__(result.tail, "event_hash", "pevt_" + "0" * 64)
    elif mode == "forged_success":
        object.__setattr__(result, "step_statuses", (("root", "succeeded", 1),))
    elif mode == "missing_running":
        object.__setattr__(result, "ambiguous_running_steps", ())
    elif mode == "list_statuses":
        object.__setattr__(result, "step_statuses", list(result.step_statuses))
    elif mode == "duplicate_statuses":
        object.__setattr__(
            result, "step_statuses",
            result.step_statuses + result.step_statuses,
        )
    else:
        raise AssertionError(f"unknown synthetic fault: {mode}")
    return result


_MODES = (
    "alien_type", "cloned_tail", "tail_event_count", "tail_hash",
    "forged_success", "missing_running", "list_statuses", "duplicate_statuses",
)


@pytest.mark.parametrize("mode", _MODES)
@pytest.mark.parametrize("operation", ("append", "recover"))
def test_snapshot_callback_cannot_forge_recovery_or_write_receipt(
    tmp_path, monkeypatch, operation, mode,
):
    journal = _journal(tmp_path)
    if operation == "recover":
        committed = journal.append(
            "root", StepState.RUNNING, expected_revision=0, at_ms=7,
        )
        expected_count = 1
        original_tail = committed.tail
    else:
        expected_count = 0
        original_tail = journal.recover().tail

    real_snapshot = journal_module._snapshot
    seen = []

    def malicious_snapshot(graph, tail):
        result = _poison(real_snapshot(graph, tail), mode)
        seen.append(mode)
        return result

    monkeypatch.setattr(journal_module, "_snapshot", malicious_snapshot)
    with pytest.raises(SyntheticPlanJournalRejected, match="recovery result"):
        if operation == "append":
            journal.append(
                "root", StepState.RUNNING, expected_revision=0, at_ms=7,
                retained=original_tail,
            )
        else:
            journal.recover(retained=original_tail)
    assert seen == [mode]
    # The pre-COMMIT append must roll back; read-only recovery cannot write.
    monkeypatch.setattr(journal_module, "_snapshot", real_snapshot)
    restored = journal.recover()
    assert restored.tail.event_count == expected_count
    assert restored.ambiguous_running_steps == (
        ("root",) if operation == "recover" else ()
    )
    assert restored.automatic_replay_authorized is False


class CommitProxy:
    """One local connection callback, never a real backend."""

    def __init__(self, connection, callback):
        self.connection = connection
        self.callback = callback

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def commit(self):
        self.connection.commit()
        self.callback()


@pytest.mark.parametrize("mode", ("cloned_tail", "forged_success", "missing_running"))
def test_postcommit_mutation_rejected_without_erasing_durable_running_event(
    tmp_path, monkeypatch, mode,
):
    journal = _journal(tmp_path)
    real_connect = journal._connect
    real_snapshot = journal_module._snapshot
    received = []

    def capture(graph, tail):
        result = real_snapshot(graph, tail)
        received.append(result)
        return result

    def open_commit_proxy(*, create=False):
        return CommitProxy(
            real_connect(create=create),
            lambda: _poison(received[-1], mode),
        )

    monkeypatch.setattr(journal_module, "_snapshot", capture)
    monkeypatch.setattr(journal, "_connect", open_commit_proxy)
    with pytest.raises(SyntheticPlanJournalRejected, match="recovery result"):
        journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=9)
    assert len(received) == 1

    # SQLite commit already succeeded. A later failure cannot authorize a
    # second WRITE attempt or silently turn this event into PENDING.
    monkeypatch.setattr(journal_module, "_snapshot", real_snapshot)
    restored = journal.recover()
    assert restored.tail.event_count == 1
    assert restored.ambiguous_running_steps == ("root",)
    assert restored.automatic_replay_authorized is False
    assert restored.dispatch_authorized is False


def test_stable_snapshot_returns_exact_running_witness(tmp_path):
    journal = _journal(tmp_path)
    before = journal.recover()
    after = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=9,
        retained=before.tail,
    )
    assert after.step_statuses == (("root", "running", 1),)
    assert after.ambiguous_running_steps == ("root",)
    assert journal.recover(retained=after.tail) == after
    assert after.automatic_replay_authorized is False
