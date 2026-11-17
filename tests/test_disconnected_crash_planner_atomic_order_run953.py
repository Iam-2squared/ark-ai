"""Run953: two local journals retain crash order without authorizing replay.

These are disposable, independent SQLite fixtures. Their readback is not an
atomic cross-store receipt, an authenticated approval, or external execution.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys

import pytest

from ark.agency import PlanStep, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("synthetic.read", "synthetic.read", "local-only")
    return (PlanStep("write", call), PlanStep("independent", call))


@pytest.mark.parametrize("reserve_after_running", (False, True))
def test_abrupt_exit_between_independent_plan_and_audit_commits(
    tmp_path, reserve_after_running: bool,
) -> None:
    plan_path = tmp_path / "synthetic-plan.sqlite3"
    audit_path = tmp_path / "synthetic-preaction.sqlite3"
    original_tail = SyntheticPlanJournal(plan_path, _steps()).recover().tail

    child = """
import os
import sys
from pathlib import Path
from ark.agency import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim, DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
call = ToolCall("synthetic.read", "synthetic.read", "local-only")
steps = (PlanStep("write", call), PlanStep("independent", call))
journal = SyntheticPlanJournal(Path(sys.argv[1]), steps)
ledger = DisconnectedAtomicPreactionLedger.create(Path(sys.argv[2]))
journal.append(
    "write", StepState.RUNNING, expected_revision=0,
    at_ms=100, retained=journal.recover().tail,
)
if sys.argv[3] == "yes":
    ledger.reserve(
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "a" * 64, "a" * 64),
        retained=genesis_atomic_preaction_witness(),
    )
os._exit(37)
"""
    completed = subprocess.run(
        [
            sys.executable, "-c", child, str(plan_path), str(audit_path),
            "yes" if reserve_after_running else "no",
        ],
        text=True, capture_output=True, check=False, timeout=30,
    )
    assert completed.returncode == 37, completed.stderr

    with sqlite3.connect(plan_path) as conn:
        plan_rows = conn.execute(
            "SELECT seq,step_id,to_state FROM synthetic_plan_events ORDER BY seq"
        ).fetchall()
    with sqlite3.connect(audit_path) as conn:
        intent_rows = conn.execute(
            "SELECT seq,occurrence_id,chain_sha256 FROM intents ORDER BY seq"
        ).fetchall()
        audit_rows = conn.execute(
            "SELECT seq FROM preaction_audit ORDER BY seq"
        ).fetchall()

    assert plan_rows == [(1, "write", "running")]
    assert len(intent_rows) == len(audit_rows) == int(reserve_after_running)

    # A cold recovery can report both histories, but cannot infer what an
    # external executor did, nor upgrade RUNNING to PENDING or SUCCEEDED.
    recovered = SyntheticPlanJournal(plan_path, _steps()).recover(
        retained=original_tail,
    )
    assert recovered.ambiguous_running_steps == ("write",)
    assert dict(
        (name, (state, revision))
        for name, state, revision in recovered.step_statuses
    ) == {"write": ("running", 1), "independent": ("pending", 0)}
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    # This witness is intentionally reconstructed from the SAME local DB.
    # Its successful diagnostic inspection is not independent custody.
    witness = (
        AtomicPreactionWitness(1, intent_rows[0][2])
        if reserve_after_running else genesis_atomic_preaction_witness()
    )
    snapshot = DisconnectedAtomicPreactionLedger(audit_path).inspect(witness)
    assert snapshot.occurrence_ids == (
        ("occ_" + "a" * 64,) if reserve_after_running else ()
    )
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False

    # Repeated cold reviews must never mutate either independently committed
    # history or synthesize a cross-store transaction.
    SyntheticPlanJournal(plan_path, _steps()).recover(retained=original_tail)
    DisconnectedAtomicPreactionLedger(audit_path).inspect(witness)
    with sqlite3.connect(plan_path) as conn:
        assert conn.execute(
            "SELECT seq,step_id,to_state FROM synthetic_plan_events ORDER BY seq"
        ).fetchall() == plan_rows
    with sqlite3.connect(audit_path) as conn:
        assert conn.execute(
            "SELECT seq,occurrence_id,chain_sha256 FROM intents ORDER BY seq"
        ).fetchall() == intent_rows
