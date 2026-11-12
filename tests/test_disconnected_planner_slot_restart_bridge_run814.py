"""Cross-check a recovered Planner against real local SQLite WRITE slots."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_planner_slot_restart_bridge as bridge
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

_PLAN = "plan_" + "a" * 64
_WRITE = "step_" + "0" * 16
_READ = "step_" + "1" * 16
_REQUEST = "c" * 64
_SLOT = derive_disconnected_write_slot_id(_PLAN, _WRITE, _REQUEST)
_TAIL = SyntheticPlanTail(
    _PLAN, 0, "pevt_" + "b" * 64, "pstate_" + "d" * 64, -1,
)
_CLAIMS = (
    DisconnectedDependencyClaim(_WRITE, Effect.WRITE, StepState.RUNNING),
    DisconnectedDependencyClaim(
        _READ, Effect.READ, StepState.PENDING, (_WRITE,),
    ),
)
_ROWS = (
    SyntheticWriteStoreObservation(
        _WRITE, "running", "present", "absent", "unavailable",
    ),
)


def _setup(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "slot-bridge.sqlite", create=True)
    genesis = genesis_write_slot_witness()
    retained = ledger.reserve_many(
        (DetachedWriteSlotClaim(_SLOT, _PLAN, _WRITE, _REQUEST),),
        retained=genesis,
    ).witness
    projection = review_disconnected_dependency_quarantine(
        topology_digest=_PLAN,
        claims=_CLAIMS,
        independently_expected_write_ids=(_WRITE,),
        observations=_ROWS,
    )
    recovered = SyntheticPlanRecovery(
        _TAIL,
        ((_WRITE, "running", 0), (_READ, "pending", 0)),
        (_WRITE,),
    )
    return {
        "ledger": DisconnectedWriteSlotLedger(tmp_path / "slot-bridge.sqlite"),
        "retained_slot_witness": retained,
        "recovered": recovered,
        "retained_tail": _TAIL,
        "claims": _CLAIMS,
        "independently_expected_write_ids": (_WRITE,),
        "observations": _ROWS,
        "dependency": projection,
        "offline_steps": (
            OfflineRecoveryStepClaim(_WRITE, "WRITE", (), "RUNNING", None, _SLOT),
            OfflineRecoveryStepClaim(_READ, "READ", (_WRITE,), "PENDING"),
        ),
    }


def test_join_all_steps_and_durable_write_slot_remain_held(tmp_path):
    data = _setup(tmp_path)
    result = bridge.review_disconnected_planner_slot_restart(**data)
    assert result == bridge.review_disconnected_planner_slot_restart(**data)
    assert result.plan_id == _PLAN
    assert result.held_step_ids == (_WRITE, _READ)
    assert result.unknown_step_ids == (_WRITE,)
    assert result.reserved_write_count == 1
    assert len(result.bridge_sha256) == 64
    assert len(result.bundle_sha256) == 64
    assert len(result.slot_fingerprint) == 64
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_authenticated is False
    assert result.cross_store_atomicity_proven is False
    assert result.external_outcome_verified is False


@pytest.mark.parametrize(
    "changed",
    (
        "missing-write", "missing-step", "duplicate-step", "read-becomes-write",
        "wrong-state", "wrong-dependency", "wrong-slot", "missing-slot",
        "false-reservation", "unknown-reservation", "stale-tip",
        "journal-mismatch", "wrong-observation-state",
    ),
)
def test_reject_cross_source_mismatch_without_releasing_write(tmp_path, changed):
    data = _setup(tmp_path)
    steps = data["offline_steps"]
    if changed == "missing-write":
        data["independently_expected_write_ids"] = ()
    elif changed == "missing-step":
        data["offline_steps"] = steps[:1]
    elif changed == "duplicate-step":
        data["offline_steps"] = (steps[0], steps[0])
    elif changed == "read-becomes-write":
        data["offline_steps"] = (
            steps[0], replace(steps[1], effect="WRITE"),
        )
    elif changed == "wrong-state":
        data["offline_steps"] = (
            replace(steps[0], state="PENDING"), steps[1],
        )
    elif changed == "wrong-dependency":
        data["offline_steps"] = (steps[0], replace(steps[1], depends_on=()))
    elif changed == "wrong-slot":
        data["offline_steps"] = (
            replace(steps[0], reservation_id="slot_" + "f" * 64), steps[1],
        )
    elif changed == "missing-slot":
        data["offline_steps"] = (
            replace(steps[0], reservation_id=None), steps[1],
        )
    elif changed == "false-reservation":
        data["observations"] = (
            replace(_ROWS[0], reservation="absent"),
        )
    elif changed == "unknown-reservation":
        data["observations"] = (
            replace(_ROWS[0], reservation="unavailable"),
        )
    elif changed == "stale-tip":
        data["retained_slot_witness"] = genesis_write_slot_witness()
    elif changed == "journal-mismatch":
        data["retained_tail"] = replace(
            _TAIL, event_hash="pevt_" + "f" * 64,
        )
    elif changed == "wrong-observation-state":
        data["observations"] = (
            replace(_ROWS[0], plan_state="pending"),
        )
    with pytest.raises(bridge.DisconnectedPlannerSlotBridgeRejected):
        bridge.review_disconnected_planner_slot_restart(**data)


@pytest.mark.parametrize("changed", ("recovery-review", "ledger-review", "authority"))
def test_reject_substituted_reviewers_before_running_callbacks(
    tmp_path, monkeypatch, changed,
):
    data = _setup(tmp_path)
    with monkeypatch.context() as patch:
        if changed == "recovery-review":
            patch.setattr(
                bridge.bundle_module,
                "review_disconnected_restart_receipt_bundle",
                lambda **kwargs: (_ for _ in ()).throw(
                    AssertionError("forged Planner reviewer executed")
                ),
            )
        elif changed == "ledger-review":
            patch.setattr(
                bridge.slot_module, "review_disconnected_write_restart",
                lambda *args: (_ for _ in ()).throw(
                    AssertionError("forged durable reviewer executed")
                ),
            )
        else:
            patch.setattr(
                bridge.DisconnectedPlannerSlotBridge, "dispatch_authorized",
                property(lambda _: True),
            )
        with pytest.raises(
            bridge.DisconnectedPlannerSlotBridgeRejected, match="protocol changed",
        ):
            bridge.review_disconnected_planner_slot_restart(**data)


def test_recovered_running_step_can_be_marked_unknown_but_never_replayed(tmp_path):
    data = _setup(tmp_path)
    steps = data["offline_steps"]
    data["offline_steps"] = (replace(steps[0], state="UNKNOWN"), steps[1])
    result = bridge.review_disconnected_planner_slot_restart(**data)
    assert result.unknown_step_ids == (_WRITE,)
    assert result.reserved_write_count == 1
    assert result.automatic_replay_authorized is False
