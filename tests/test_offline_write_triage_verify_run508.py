"""Detached manual-only WRITE packet checksum and authority-denial tests."""

from dataclasses import replace

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)
from ark.agency.offline_write_manual_triage import (
    OfflineWriteTriageItem,
    OfflineWriteTriagePacket,
    build_offline_write_triage_packet,
)
from ark.agency.offline_write_triage_verify import (
    OfflineWriteTriageVerificationRejected,
    verify_offline_write_triage_packet,
)

PLAN = "plan_" + "a" * 64
ONE = "step_" + "1" * 16
TWO = "step_" + "2" * 16
RESULT = "f" * 64


def _packet(tmp_path, state="UNKNOWN", *, result=None):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "slots.db").resolve(), create=True,
    )
    witness = genesis_write_slot_witness()
    steps = (OfflineRecoveryStepClaim(ONE, "WRITE", (), state, result),)
    return build_offline_write_triage_packet(ledger, witness, PLAN, steps), witness


@pytest.mark.parametrize(
    ("state", "result"),
    [
        ("UNKNOWN", None),
        ("RUNNING", None),
        ("PENDING", None),
        ("FAILED", None),
        ("CANCELLED", None),
        ("BLOCKED", None),
        ("SUCCEEDED", RESULT),
    ],
)
def test_valid_checklist_is_inert_and_repeatable(tmp_path, state, result):
    packet, witness = _packet(tmp_path, state, result=result)
    first = verify_offline_write_triage_packet(packet, witness)
    second = verify_offline_write_triage_packet(packet, witness)
    assert first == second
    assert first.item_count == 1
    assert first.packet_sha256 == packet.packet_sha256
    assert first.independently_authenticated is False
    assert first.human_review_completed is False
    assert first.external_outcome_verified is False
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False


@pytest.mark.parametrize(
    "changes",
    [
        {"plan_id": "plan_" + "b" * 64},
        {"packet_sha256": "0" * 64},
        {"recovery_fingerprint": "1" * 64},
        {"reservation_chain_sha256": "2" * 64},
        {"items": ()},
        {"items": (OfflineWriteTriageItem(
            ONE, "UNKNOWN", "READY_MOCK_ONLY", None, "UNKNOWN_EFFECT_HOLD",
        ),)},
        {"items": (OfflineWriteTriageItem(
            ONE, "UNKNOWN", "QUARANTINE_WRITE_UNKNOWN", None, "CLAIMED_OUTCOME_REVIEW_ONLY",
        ),)},
        {"items": (OfflineWriteTriageItem(
            ONE, "SUCCEEDED", "COMPLETE_UNVERIFIED", None, "CLAIMED_OUTCOME_REVIEW_ONLY",
        ),)},
        {"items": (OfflineWriteTriageItem(
            ONE, "UNKNOWN", "QUARANTINE_WRITE_UNKNOWN", None, "UNKNOWN_EFFECT_HOLD",
        ),) * 2},
        {"items": (OfflineWriteTriageItem(
            TWO, "PENDING", "HELD_WRITE_APPROVAL", None, "CLAIMED_OUTCOME_REVIEW_ONLY",
        ),)},
    ],
)
def test_modified_detached_packet_is_rejected(tmp_path, changes):
    packet, witness = _packet(tmp_path)
    forged = replace(packet, **changes)
    with pytest.raises(OfflineWriteTriageVerificationRejected):
        verify_offline_write_triage_packet(forged, witness)


def test_changed_witness_epoch_does_not_rebind_old_packet(tmp_path):
    packet, witness = _packet(tmp_path)
    with pytest.raises(OfflineWriteTriageVerificationRejected):
        verify_offline_write_triage_packet(packet, replace(witness, count=1))


def test_packet_type_and_witness_type_are_exact(tmp_path):
    packet, witness = _packet(tmp_path)
    with pytest.raises(OfflineWriteTriageVerificationRejected):
        verify_offline_write_triage_packet(object(), witness)
    with pytest.raises(OfflineWriteTriageVerificationRejected):
        verify_offline_write_triage_packet(packet, object())


def test_reflected_dispatch_authority_is_rejected(tmp_path, monkeypatch):
    packet, witness = _packet(tmp_path)
    monkeypatch.setattr(
        OfflineWriteTriagePacket, "dispatch_authorized",
        property(lambda self: True),
    )
    with pytest.raises(OfflineWriteTriageVerificationRejected, match="authority"):
        verify_offline_write_triage_packet(packet, witness)


def test_late_mutation_in_inert_flag_getter_is_rejected(tmp_path, monkeypatch):
    packet, witness = _packet(tmp_path)

    def mutate(self):
        object.__setattr__(self, "packet_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        OfflineWriteTriagePacket, "human_review_completed", property(mutate),
    )
    with pytest.raises(OfflineWriteTriageVerificationRejected):
        verify_offline_write_triage_packet(packet, witness)


def test_duplicate_step_or_bad_reservation_never_validates(tmp_path):
    packet, witness = _packet(tmp_path)
    original = packet.items[0]
    for bad_items in (
        (original, original),
        (replace(original, reservation_id="slot_" + "g" * 64),),
        (replace(original, claimed_state="PENDING"),),
    ):
        with pytest.raises(OfflineWriteTriageVerificationRejected):
            verify_offline_write_triage_packet(replace(packet, items=bad_items), witness)
