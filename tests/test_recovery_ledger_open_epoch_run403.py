"""Cross-store synthetic WRITE triage rejects drift at ledger open boundaries.

All diagnostics use isolated local SQLite fixtures. They never dispatch a
backend, authorize replay, or establish an external exactly-once outcome.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.agency.synthetic_recovery_triage as recovery
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, _call):
        raise AssertionError("cross-store recovery must never dispatch")


def _fixture(tmp_path: Path):
    call = ToolCall("offline", "write", "local", {"fixture": True})
    registry = ToolRegistry((
        ToolRegistration("offline", "write", Effect.WRITE, "mock", NeverBackend()),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    ledger_path = tmp_path / "reservations.sqlite"
    SyntheticOccurrenceStore(ledger_path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    return journal, ledger_path, audit, registry, call


def _review(state):
    journal, ledger_path, audit, registry, call = state
    return recovery.review_synthetic_write_recovery(
        journal, ledger_path, audit, registry, call, step_id="root",
    )


def _mutate(state, target):
    journal, _ledger_path, audit, _registry, call = state
    if target == "call":
        object.__setattr__(call, "scope", "changed-scope")
    elif target == "journal":
        journal._path = Path(str(journal._path))
    else:
        audit.path = Path(str(audit.path))


@pytest.mark.parametrize("boundary", ("resolve", "as_uri", "connect"))
@pytest.mark.parametrize("target", ("call", "journal", "audit"))
def test_ledger_open_rejects_drift_before_later_audit_can_restore_it(
    tmp_path: Path, monkeypatch, boundary: str, target: str,
):
    state = _fixture(tmp_path)
    ledger_path = state[1]
    invoked = []
    opened = []

    if boundary == "connect":
        original = sqlite3.connect

        def connecting(*args, **kwargs):
            connection = original(*args, **kwargs)
            if str(ledger_path.name) in str(args[0]) and "mode=ro" in str(args[0]):
                invoked.append(boundary)
                opened.append(connection)
                _mutate(state, target)
            return connection

        monkeypatch.setattr(recovery.sqlite3, "connect", connecting)
    else:
        original = getattr(Path, boundary)

        def resolving(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            matches = (
                path is ledger_path if boundary == "resolve"
                else path == ledger_path
            )
            if matches:
                invoked.append(boundary)
                _mutate(state, target)
            return result

        monkeypatch.setattr(Path, boundary, resolving)

    with pytest.raises(
        recovery.SyntheticRecoveryRejected, match="input|source|incomplete",
    ):
        _review(state)
    assert invoked == [boundary]
    for connection in opened:
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            connection.execute("SELECT 1")


def test_stable_ledger_open_is_an_inert_pending_diagnosis(tmp_path: Path):
    result = _review(_fixture(tmp_path))
    assert result.step_state == "pending"
    assert result.matching_occurrences == ()
    assert result.dispatch_authorized is False
    assert result.external_outcome_known is False
    assert result.automatic_replay_authorized is False
