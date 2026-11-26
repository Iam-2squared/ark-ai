"""Reentrant cross-epoch Planner drift must not be accepted as a WRITE recovery."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_planner_slot_restart_bridge as bridge
from ark.agency.contracts import Effect, StepState
from ark.agency.disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    review_disconnected_dependency_quarantine,
)
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)
from ark.agency.planner_journal_review import SyntheticPlanRecovery, SyntheticPlanTail
from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticWriteStoreObservation,
)


def _case(tmp_path):
    plan = "plan_" + "a" * 64
    write = "step_" + "0" * 16
    read = "step_" + "1" * 16
    slot = derive_disconnected_write_slot_id(plan, write, "c" * 64)
    tail = SyntheticPlanTail(plan, 0, "pevt_" + "b" * 64,
                             "pstate_" + "d" * 64, -1)
    claims = (
        DisconnectedDependencyClaim(write, Effect.WRITE, StepState.RUNNING),
        DisconnectedDependencyClaim(
            read, Effect.READ, StepState.PENDING, (write,),
        ),
    )
    observations = (
        SyntheticWriteStoreObservation(
            write, "running", "present", "absent", "unavailable",
        ),
    )
    ledger_path = tmp_path / "restart-epoch.sqlite"
    writer = DisconnectedWriteSlotLedger(ledger_path, create=True)
    witness = writer.reserve_many(
        (DetachedWriteSlotClaim(slot, plan, write, "c" * 64),),
        retained=genesis_write_slot_witness(),
    ).witness
    return {
        "ledger": DisconnectedWriteSlotLedger(ledger_path),
        "retained_slot_witness": witness,
        "recovered": SyntheticPlanRecovery(
            tail, ((write, "running", 0), (read, "pending", 0)), (write,),
        ),
        "retained_tail": tail,
        "claims": claims,
        "independently_expected_write_ids": (write,),
        "observations": observations,
        "dependency": review_disconnected_dependency_quarantine(
            topology_digest=plan,
            claims=claims,
            independently_expected_write_ids=(write,),
            observations=observations,
        ),
        "offline_steps": (
            OfflineRecoveryStepClaim(write, "WRITE", (), "RUNNING", None, slot),
            OfflineRecoveryStepClaim(read, "READ", (write,), "PENDING"),
        ),
    }


def test_inert_unmodified_cross_epoch_review(tmp_path):
    result = bridge.review_disconnected_planner_slot_restart(**_case(tmp_path))
    assert result.reserved_write_count == 1
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize(
    "field",
    (
        "write-state", "read-parent", "observation-audit",
        "recovery-statuses", "tail-hash", "dependency-digest",
    ),
)
def test_late_source_mutation_during_sqlite_review_is_rejected(
    tmp_path, monkeypatch, field,
):
    data = _case(tmp_path)
    original_open = data["ledger"]._open

    def tamper_then_open(*, read_only):
        if field == "write-state":
            object.__setattr__(
                data["claims"][0], "state", StepState.PENDING,
            )
        elif field == "read-parent":
            object.__setattr__(data["claims"][1], "depends_on", ())
        elif field == "observation-audit":
            object.__setattr__(data["observations"][0], "preaction_audit", "present")
        elif field == "recovery-statuses":
            object.__setattr__(
                data["recovered"], "step_statuses",
                ((data["claims"][0].step_id, "failed", 0),
                 (data["claims"][1].step_id, "pending", 0)),
            )
        elif field == "tail-hash":
            object.__setattr__(
                data["retained_tail"], "event_hash", "pevt_" + "e" * 64,
            )
        else:
            object.__setattr__(
                data["dependency"], "digest", "f" * 64,
            )
        return original_open(read_only=read_only)

    monkeypatch.setattr(data["ledger"], "_open", tamper_then_open)
    with pytest.raises(
        bridge.DisconnectedPlannerSlotBridgeRejected,
        match="source carriers changed",
    ):
        bridge.review_disconnected_planner_slot_restart(**data)
