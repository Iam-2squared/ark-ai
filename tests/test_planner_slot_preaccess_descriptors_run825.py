"""Planner restart rejects swapped dataclass descriptors before private review.

A malicious class property must not run while a recovered DAG, offline WRITE
claims or durable SQLite witness is being inspected. Only synthetic fixtures.
"""

from __future__ import annotations

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


def _setup(tmp_path):
    path = tmp_path / "synthetic-write.sqlite"
    ledger = DisconnectedWriteSlotLedger(path, create=True)
    witness = ledger.reserve_many(
        (DetachedWriteSlotClaim(_SLOT, _PLAN, _WRITE, _REQUEST),),
        retained=genesis_write_slot_witness(),
    ).witness
    tail = SyntheticPlanTail(
        _PLAN, 0, "pevt_" + "b" * 64, "pstate_" + "d" * 64, -1,
    )
    claims = (
        DisconnectedDependencyClaim(_WRITE, Effect.WRITE, StepState.RUNNING),
        DisconnectedDependencyClaim(
            _READ, Effect.READ, StepState.PENDING, (_WRITE,),
        ),
    )
    observations = (
        SyntheticWriteStoreObservation(
            _WRITE, "running", "present", "absent", "unavailable",
        ),
    )
    projection = review_disconnected_dependency_quarantine(
        topology_digest=_PLAN,
        claims=claims,
        independently_expected_write_ids=(_WRITE,),
        observations=observations,
    )
    return {
        "ledger": DisconnectedWriteSlotLedger(path),
        "retained_slot_witness": witness,
        "recovered": SyntheticPlanRecovery(
            tail, ((_WRITE, "running", 0), (_READ, "pending", 0)), (_WRITE,),
        ),
        "retained_tail": tail,
        "claims": claims,
        "independently_expected_write_ids": (_WRITE,),
        "observations": observations,
        "dependency": projection,
        "offline_steps": (
            OfflineRecoveryStepClaim(_WRITE, "WRITE", (), "RUNNING", None, _SLOT),
            OfflineRecoveryStepClaim(_READ, "READ", (_WRITE,), "PENDING"),
        ),
    }


@pytest.mark.parametrize(
    ("carrier", "field"),
    (
        ("DisconnectedDependencyClaim", "step_id"),
        ("DisconnectedDependencyClaim", "depends_on"),
        ("DisconnectedDependencyProjection", "holds"),
        ("OfflineRecoveryStepClaim", "reservation_id"),
        ("SyntheticWriteStoreObservation", "plan_state"),
        ("SyntheticPlanRecovery", "step_statuses"),
        ("SyntheticPlanTail", "event_hash"),
        ("WriteSlotLedgerWitness", "chain_sha256"),
    ),
)
def test_swapped_source_slot_refused_before_executing_getter(
    tmp_path, monkeypatch, carrier, field,
):
    data = _setup(tmp_path)
    invoked = []

    def hostile_getter(_):
        invoked.append((carrier, field))
        raise AssertionError("hostile Planner receipt getter executed")

    cls = getattr(bridge, carrier)
    with monkeypatch.context() as patch:
        patch.setattr(cls, field, property(hostile_getter))
        with pytest.raises(
            bridge.DisconnectedPlannerSlotBridgeRejected,
            match="protocol changed",
        ):
            bridge.review_disconnected_planner_slot_restart(**data)
    assert invoked == []


@pytest.mark.parametrize(
    "carrier", ("OfflineRecoveryStepClaim", "SyntheticPlanRecovery"),
)
def test_replaced_input_class_refused_without_sqlite_access(
    tmp_path, monkeypatch, carrier,
):
    data = _setup(tmp_path)

    class Forged:
        def __getattribute__(self, _name):
            raise AssertionError("forged class getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(bridge, carrier, Forged)
        with pytest.raises(
            bridge.DisconnectedPlannerSlotBridgeRejected,
            match="protocol changed",
        ):
            bridge.review_disconnected_planner_slot_restart(**data)


def test_original_restart_protocol_still_holds_all_writes(tmp_path):
    data = _setup(tmp_path)
    result = bridge.review_disconnected_planner_slot_restart(**data)
    assert result.held_step_ids == (_WRITE, _READ)
    assert result.unknown_step_ids == (_WRITE,)
    assert result.automatic_replay_authorized is False
    assert result.dispatch_authorized is False
    assert result.cross_store_atomicity_proven is False
