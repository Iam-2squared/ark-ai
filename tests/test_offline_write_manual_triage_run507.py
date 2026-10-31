"""No synthetic recovery checklist may authorize or replay an external WRITE."""

import sqlite3

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)
from ark.agency.offline_write_manual_triage import (
    OfflineWriteTriageRejected,
    build_offline_write_triage_packet,
)

PLAN = "plan_" + "a" * 64
ONE = "step_" + "1" * 16
TWO = "step_" + "2" * 16
THREE = "step_" + "3" * 16
HASH = "c" * 64


def _ledger(tmp_path):
    return DisconnectedWriteSlotLedger((tmp_path / "write-slots.db").resolve(), create=True)


def _step(step_id=ONE, *, state="UNKNOWN", effect="WRITE", depends_on=(), result=None):
    return OfflineRecoveryStepClaim(step_id, effect, depends_on, state, result)


@pytest.mark.parametrize(
    ("state", "result", "expected"),
    [
        ("UNKNOWN", None, "UNKNOWN_EFFECT_HOLD"),
        ("RUNNING", None, "UNKNOWN_EFFECT_HOLD"),
        ("PENDING", None, "CLAIMED_OUTCOME_REVIEW_ONLY"),
        ("FAILED", None, "CLAIMED_OUTCOME_REVIEW_ONLY"),
        ("SUCCEEDED", HASH, "CLAIMED_OUTCOME_REVIEW_ONLY"),
    ],
)
def test_write_states_never_grant_retry(tmp_path, state, result, expected):
    ledger = _ledger(tmp_path)
    retained = genesis_write_slot_witness()
    packet = build_offline_write_triage_packet(
        ledger, retained, PLAN, (_step(state=state, result=result),),
    )
    assert len(packet.items) == 1
    assert packet.items[0].investigation == expected
    assert packet.items[0].claimed_state == state
    assert packet.items[0].disposition != "READY_MOCK_ONLY"
    assert packet.dispatch_authorized is False
    assert packet.automatic_replay_authorized is False
    assert packet.external_outcome_verified is False
    assert packet.human_review_completed is False
    assert packet.reservation_chain_sha256 == retained.chain_sha256


def test_mixed_read_write_only_lists_write_in_dependency_order(tmp_path):
    ledger = _ledger(tmp_path)
    steps = (
        _step(ONE, effect="READ", state="SUCCEEDED", result=HASH),
        _step(TWO, state="UNKNOWN", depends_on=(ONE,)),
        _step(THREE, state="PENDING", depends_on=(ONE,)),
    )
    packet = build_offline_write_triage_packet(
        ledger, genesis_write_slot_witness(), PLAN, steps,
    )
    assert tuple(item.step_id for item in packet.items) == (TWO, THREE)
    assert packet.items[0].disposition == "QUARANTINE_WRITE_UNKNOWN"
    assert packet.items[1].disposition == "HELD_WRITE_APPROVAL"
    assert len(packet.packet_sha256) == 64


def test_repeated_readonly_review_is_deterministic(tmp_path):
    ledger = _ledger(tmp_path)
    steps = (_step(),)
    witness = genesis_write_slot_witness()
    with sqlite3.connect(ledger._path) as conn:
        before = tuple(conn.iterdump())
    a = build_offline_write_triage_packet(ledger, witness, PLAN, steps)
    b = build_offline_write_triage_packet(ledger, witness, PLAN, steps)
    assert a == b
    with sqlite3.connect(ledger._path) as conn:
        assert tuple(conn.iterdump()) == before


@pytest.mark.parametrize(
    "claims",
    [
        (),
        (_step(ONE), _step(ONE)),
        (_step(ONE, state="SUCCEEDED")),
        (_step(ONE, state="RUNNING", result=HASH)),
        (_step(ONE, depends_on=(TWO,)),),
    ],
)
def test_invalid_recovery_claims_fail_closed(tmp_path, claims):
    ledger = _ledger(tmp_path)
    with pytest.raises(OfflineWriteTriageRejected):
        build_offline_write_triage_packet(
            ledger, genesis_write_slot_witness(), PLAN, claims,
        )


def test_unretained_slot_claim_never_becomes_manual_permission(tmp_path):
    ledger = _ledger(tmp_path)
    forged = OfflineRecoveryStepClaim(
        ONE, "WRITE", (), "UNKNOWN", None, "slot_" + "b" * 64,
    )
    with pytest.raises(OfflineWriteTriageRejected):
        build_offline_write_triage_packet(
            ledger, genesis_write_slot_witness(), PLAN, (forged,),
        )


def test_read_only_claim_has_empty_operator_queue(tmp_path):
    ledger = _ledger(tmp_path)
    packet = build_offline_write_triage_packet(
        ledger, genesis_write_slot_witness(), PLAN,
        (_step(effect="READ", state="PENDING"),),
    )
    assert packet.items == ()
    assert packet.automatic_replay_authorized is False
