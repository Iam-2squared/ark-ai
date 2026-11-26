"""An offline WRITE triage checklist cannot mutate after the last denial.

These are disconnected SQLite fixtures, not human approvals or live effects.
No external WRITE, authorization, automatic replay or cleanup is attempted.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)
from ark.agency.offline_write_manual_triage import (
    OfflineWriteTriagePacket,
    OfflineWriteTriageRejected,
    build_offline_write_triage_packet,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "b" * 16


def fixture(tmp_path):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "last-denial-write.db").resolve(), create=True,
    )
    retained = genesis_write_slot_witness()
    steps = (OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN", None),)
    return ledger, retained, steps


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("step_id", "step_" + "c" * 16),
        ("claimed_state", "SUCCEEDED"),
        ("disposition", "READY_MOCK_ONLY"),
        ("reservation_id", "slot_" + "d" * 64),
        ("investigation", "CLAIMED_OUTCOME_REVIEW_ONLY"),
    ),
)
def test_false_denial_getter_cannot_change_nested_checklist(
    tmp_path, monkeypatch, field, value,
):
    ledger, retained, steps = fixture(tmp_path)

    def tampered(self):
        object.__setattr__(self.items[0], field, value)
        return False

    monkeypatch.setattr(
        OfflineWriteTriagePacket, "automatic_replay_authorized",
        property(tampered),
    )
    with pytest.raises(OfflineWriteTriageRejected, match="packet|authority"):
        build_offline_write_triage_packet(ledger, retained, PLAN, steps)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("plan_id", "plan_" + "f" * 64),
        ("items", ()),
        ("reservation_chain_sha256", "f" * 64),
        ("recovery_fingerprint", "f" * 64),
        ("packet_sha256", "f" * 64),
    ),
)
def test_false_denial_getter_cannot_change_packet_fields(
    tmp_path, monkeypatch, field, value,
):
    ledger, retained, steps = fixture(tmp_path)

    def tampered(self):
        object.__setattr__(self, field, value)
        return False

    monkeypatch.setattr(
        OfflineWriteTriagePacket, "automatic_replay_authorized",
        property(tampered),
    )
    with pytest.raises(OfflineWriteTriageRejected, match="packet|authority"):
        build_offline_write_triage_packet(ledger, retained, PLAN, steps)


def test_unmodified_unknown_write_remains_manual_only(tmp_path):
    ledger, retained, steps = fixture(tmp_path)
    packet = build_offline_write_triage_packet(ledger, retained, PLAN, steps)
    assert len(packet.items) == 1
    assert packet.items[0].claimed_state == "UNKNOWN"
    assert packet.items[0].investigation == "UNKNOWN_EFFECT_HOLD"
    assert packet.dispatch_authorized is False
    assert packet.automatic_replay_authorized is False
    assert packet.external_outcome_verified is False
    assert packet.human_review_completed is False
