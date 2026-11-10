"""True child-process exits after each independent mock WRITE commit.

This is an inert, four-SQLite fixture. The child exits without returning a
receipt; local RUNNING/UNKNOWN must never become authorization to replay.
No registered backend is invoked or external side effect is claimed.
"""

from __future__ import annotations

import hashlib
import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)


class _NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("a mock-only restart must not dispatch a backend")


def _state(root: Path):
    call = ToolCall("fixture.write", "offline.write", "local", {"private": "secret-only"})
    steps = (PlanStep("root", call),)
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE, "inert-v1", _NeverExecute(),
        ),
    ))
    return (
        call,
        registry,
        SyntheticPlanJournal(root / "plan.sqlite", steps),
        SyntheticOccurrenceStore(root / "occurrences.sqlite"),
        SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 12),
        SyntheticOccurrenceAuditLinkStore(root / "links.sqlite"),
    )


def _cycle(state, *, token_id: str, occurrence: str):
    call, registry, journal, ledger, audit, links = state
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call,
        OneShotAuthorization(token_id, call.request_id, 1000),
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(occurrence.encode()).hexdigest(),
        now_ms=10,
        link_store=links,
    )


def _exit_immediately_after_commit(root: str, boundary: str) -> None:
    state = _state(Path(root))
    journal, ledger, audit, links = state[2:]
    target, method = {
        "running": (journal, "append"),
        "reservation": (ledger, "reserve_synthetic"),
        "audit": (audit, "append"),
        "link": (links, "link_synthetic"),
        "terminal": (journal, "append"),
    }[boundary]
    original = getattr(target, method)

    def commit_then_exit(*args, **kwargs):
        receipt = original(*args, **kwargs)
        if boundary == "terminal" and args[1] is not StepState.SUCCEEDED:
            return receipt
        os._exit(0)  # Durable COMMIT happened; no Python callback or receipt.

    setattr(target, method, commit_then_exit)
    _cycle(state, token_id="initial", occurrence="initial")
    os._exit(91)  # A normal return would invalidate the interruption fixture.


@pytest.mark.parametrize(
    ("boundary", "counts", "status", "revision"),
    (
        ("running", (0, 0, 0), "running", 1),
        ("reservation", (1, 0, 0), "running", 1),
        ("audit", (1, 1, 0), "running", 1),
        ("link", (1, 1, 1), "running", 1),
        ("terminal", (1, 1, 1), "succeeded", 2),
    ),
)
def test_real_process_exit_does_not_reauthorize_mock_write(
    tmp_path: Path, boundary, counts, status, revision,
):
    _state(tmp_path)  # Prepare the four independent SQLite stores.
    child = get_context("spawn").Process(
        target=_exit_immediately_after_commit,
        args=(str(tmp_path), boundary),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0, "child failed before the intended committed boundary"

    cold = _state(tmp_path)
    _call, _registry, journal, ledger, audit, links = cold
    recovered = journal.recover()
    assert recovered.step_statuses == (("root", status, revision),)
    assert recovered.ambiguous_running_steps == (
        ("root",) if status == "running" else ()
    )
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert (
        ledger.count_synthetic(),
        len(audit.events()),
        links.read_witness().event_count,
    ) == counts

    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _cycle(cold, token_id="fresh-not-consent", occurrence="fresh")
    assert journal.recover() == recovered
    assert (
        ledger.count_synthetic(),
        len(audit.events()),
        links.read_witness().event_count,
    ) == counts
    assert b"secret-only" not in (tmp_path / "audit.sqlite").read_bytes()
