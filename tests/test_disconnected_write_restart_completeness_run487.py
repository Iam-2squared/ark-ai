"""A Planner restart claim must cover every durable WRITE for its plan."""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_restart_binding import (
    OfflineWriteRestartRejected,
    review_disconnected_write_restart,
)
from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)


def _slot(plan: int, step: int) -> DetachedWriteSlotClaim:
    plan_id = "plan_" + f"{plan:064x}"
    step_id = "step_" + f"{step:016x}"
    request = f"{step:064x}"
    return DetachedWriteSlotClaim(
        derive_disconnected_write_slot_id(plan_id, step_id, request),
        plan_id, step_id, request,
    )


def _setup(tmp_path, *specs):
    path = tmp_path / "writes.sqlite"
    ledger = DisconnectedWriteSlotLedger(path, create=True)
    retained = genesis_write_slot_witness()
    slots = tuple(_slot(*spec) for spec in specs)
    if slots:
        retained = ledger.reserve_many(slots, retained=retained).witness
    return DisconnectedWriteSlotLedger(path), retained, slots


def _unknown(slot, *, reservation=True):
    return OfflineRecoveryStepClaim(
        slot.step_id, "WRITE", (), "UNKNOWN", None,
        slot.slot_id if reservation else None,
    )


@pytest.mark.parametrize("missing", [0, 1])
def test_partial_claim_omits_a_persisted_write(tmp_path, missing):
    ledger, retained, slots = _setup(tmp_path, (1, 1), (1, 2))
    kept = slots[1 - missing]
    with pytest.raises(OfflineWriteRestartRejected, match="unrepresented"):
        review_disconnected_write_restart(
            ledger, retained, kept.plan_id, (_unknown(kept),),
        )
    assert ledger.inspect(retained=retained) == retained


@pytest.mark.parametrize("missing", [0, 1])
def test_declared_write_without_its_persisted_reservation_is_incomplete(
    tmp_path, missing,
):
    ledger, retained, slots = _setup(tmp_path, (1, 1), (1, 2))
    steps = tuple(_unknown(s, reservation=(index != missing))
                  for index, s in enumerate(slots))
    with pytest.raises(OfflineWriteRestartRejected, match="unrepresented"):
        review_disconnected_write_restart(ledger, retained, slots[0].plan_id, steps)


def test_complete_two_write_restart_stays_quarantined(tmp_path):
    ledger, retained, slots = _setup(tmp_path, (1, 1), (1, 2))
    report = review_disconnected_write_restart(
        ledger, retained, slots[0].plan_id, tuple(_unknown(s) for s in slots),
    )
    assert (report.total_steps, report.reserved_write_steps,
            report.quarantined_write_steps) == (2, 2, 2)
    assert report.tool_dispatch_authorized is False
    assert report.write_replay_authorized is False
    assert report.external_outcome_verified is False


def test_other_plan_reservations_do_not_invalidate_complete_plan(tmp_path):
    ledger, retained, slots = _setup(tmp_path, (1, 1), (2, 2), (1, 3))
    report = review_disconnected_write_restart(
        ledger, retained, slots[0].plan_id,
        (_unknown(slots[0]), _unknown(slots[2])),
    )
    assert report.reserved_write_steps == 2
    assert report.write_replay_authorized is False


def test_foreign_plan_history_not_inferred_into_unreserved_plan(tmp_path):
    ledger, retained, slots = _setup(tmp_path, (2, 1))
    own = _slot(1, 2)
    report = review_disconnected_write_restart(
        ledger, retained, own.plan_id, (_unknown(own, reservation=False),),
    )
    assert report.reserved_write_steps == 0
    assert report.quarantined_write_steps == 1
    assert ledger.inspect(retained=retained) == retained


def test_persisted_write_cannot_be_hidden_behind_read_step(tmp_path):
    ledger, retained, slots = _setup(tmp_path, (1, 1))
    claim = OfflineRecoveryStepClaim(slots[0].step_id, "READ", (), "PENDING")
    with pytest.raises(OfflineWriteRestartRejected):
        review_disconnected_write_restart(
            ledger, retained, slots[0].plan_id, (claim,),
        )
