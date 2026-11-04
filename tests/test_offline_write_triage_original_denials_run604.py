"""Disconnected manual WRITE verification never executes counterfeit deny getters."""

from __future__ import annotations

import pytest

from ark.agency import offline_write_triage_verify as triage
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)
from ark.agency.offline_write_manual_triage import build_offline_write_triage_packet


class Counterfeit:
    def __init__(self, original, calls):
        self.original = original
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("invoked")
        return self.original if instance is None else False


def _case(tmp_path):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "local-only-slots.db").resolve(), create=True,
    )
    witness = genesis_write_slot_witness()
    step = OfflineRecoveryStepClaim("step_" + "1" * 16, "WRITE", (), "UNKNOWN", None)
    packet = build_offline_write_triage_packet(
        ledger, witness, "plan_" + "a" * 64, (step,),
    )
    return packet, witness


@pytest.mark.parametrize("flag", triage._PACKET_DENIALS)
def test_packet_counterfeit_is_rejected_before_invoking_getter(
    tmp_path, monkeypatch, flag,
):
    packet, witness = _case(tmp_path)
    calls = []
    old = vars(triage._PACKET)[flag]
    monkeypatch.setattr(triage._PACKET, flag, Counterfeit(old, calls))
    with pytest.raises(
        triage.OfflineWriteTriageVerificationRejected,
        match="authority descriptor changed",
    ):
        triage.verify_offline_write_triage_packet(packet, witness)
    assert calls == []


def test_witness_counterfeit_is_rejected_before_invoking_getter(
    tmp_path, monkeypatch,
):
    packet, witness = _case(tmp_path)
    calls = []
    old = vars(triage._WITNESS)["independently_authenticated"]
    monkeypatch.setattr(
        triage._WITNESS, "independently_authenticated", Counterfeit(old, calls),
    )
    with pytest.raises(
        triage.OfflineWriteTriageVerificationRejected,
        match="authority descriptor changed",
    ):
        triage.verify_offline_write_triage_packet(packet, witness)
    assert calls == []


@pytest.mark.parametrize("flag", triage._RESULT_DENIALS)
def test_result_counterfeit_installed_during_construction_never_runs(
    tmp_path, monkeypatch, flag,
):
    packet, witness = _case(tmp_path)
    calls = []
    report_type = triage._RESULT
    original = vars(report_type)[flag]
    old_init = report_type.__init__

    def injected_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        monkeypatch.setattr(report_type, flag, Counterfeit(original, calls))

    monkeypatch.setattr(report_type, "__init__", injected_init)
    with pytest.raises(
        triage.OfflineWriteTriageVerificationRejected,
        match="authority descriptor changed",
    ):
        triage.verify_offline_write_triage_packet(packet, witness)
    assert calls == []


def test_original_manual_write_triage_packet_remains_inert(tmp_path):
    packet, witness = _case(tmp_path)
    result = triage.verify_offline_write_triage_packet(packet, witness)
    assert result.item_count == 1
    assert result.independently_authenticated is False
    assert result.human_review_completed is False
    assert result.external_outcome_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
