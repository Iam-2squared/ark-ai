"""Manual-only WRITE packet must match live ledger and exact recovery claims."""

import sqlite3
from dataclasses import replace

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)
from ark.agency.offline_write_manual_triage import build_offline_write_triage_packet
from ark.agency.offline_write_triage_recheck import (
    OfflineWriteTriageRecheck,
    OfflineWriteTriageRecheckRejected,
    recheck_offline_write_triage,
)

PLAN = "plan_" + "a" * 64
ONE = "step_" + "1" * 16
TWO = "step_" + "2" * 16
HASH = "c" * 64


def _fixture(tmp_path, *, state="UNKNOWN", result=None):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "write-slots.db").resolve(), create=True,
    )
    retained = genesis_write_slot_witness()
    steps = (OfflineRecoveryStepClaim(ONE, "WRITE", (), state, result),)
    packet = build_offline_write_triage_packet(ledger, retained, PLAN, steps)
    return ledger, retained, steps, packet


@pytest.mark.parametrize(
    ("state", "result"),
    [
        ("UNKNOWN", None),
        ("RUNNING", None),
        ("PENDING", None),
        ("FAILED", None),
        ("CANCELLED", None),
        ("BLOCKED", None),
        ("SUCCEEDED", HASH),
    ],
)
def test_live_recheck_remains_manual_only(tmp_path, state, result):
    ledger, retained, steps, packet = _fixture(tmp_path, state=state, result=result)
    with sqlite3.connect(ledger._path) as conn:
        before = tuple(conn.iterdump())
    first = recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)
    assert first == recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)
    assert first.write_count == 1
    assert first.uncertain_write_count == int(state in {"UNKNOWN", "RUNNING"})
    assert first.packet_sha256 == packet.packet_sha256
    assert first.independent_human_review_proven is False
    assert first.external_effect_proven is False
    assert first.dispatch_authorized is False
    assert first.replay_authorized is False
    with sqlite3.connect(ledger._path) as conn:
        assert tuple(conn.iterdump()) == before


def test_same_valid_packet_does_not_bind_different_claims(tmp_path):
    ledger, retained, steps, packet = _fixture(tmp_path)
    other_steps = (replace(steps[0], state="PENDING"),)
    with pytest.raises(OfflineWriteTriageRecheckRejected, match="mismatch"):
        recheck_offline_write_triage(ledger, retained, PLAN, other_steps, packet)


def test_recheck_requires_every_write_claim_including_dependency(tmp_path):
    ledger = DisconnectedWriteSlotLedger((tmp_path / "slots.db").resolve(), create=True)
    retained = genesis_write_slot_witness()
    steps = (
        OfflineRecoveryStepClaim(ONE, "READ", (), "SUCCEEDED", HASH),
        OfflineRecoveryStepClaim(TWO, "WRITE", (ONE,), "UNKNOWN", None),
    )
    packet = build_offline_write_triage_packet(ledger, retained, PLAN, steps)
    result = recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)
    assert result.write_count == 1
    assert result.uncertain_write_count == 1
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, PLAN, steps[1:], packet)


def test_stale_retained_witness_cannot_validate_against_changed_ledger(tmp_path):
    ledger, retained, steps, packet = _fixture(tmp_path)
    slot = derive_disconnected_write_slot_id(PLAN, ONE, HASH)
    ledger.reserve_many(
        (DetachedWriteSlotClaim(slot, PLAN, ONE, HASH),), retained=retained,
    )
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)


def test_corrupt_sqlite_schema_is_not_accepted_by_live_recheck(tmp_path):
    ledger, retained, steps, packet = _fixture(tmp_path)
    with sqlite3.connect(ledger._path) as conn:
        conn.execute("PRAGMA user_version=7")
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)


@pytest.mark.parametrize(
    "bad",
    [
        "wrong",
        "plan_" + "0" * 64,
    ],
)
def test_wrong_plan_identity_is_denied(tmp_path, bad):
    ledger, retained, steps, packet = _fixture(tmp_path)
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, bad, steps, packet)


def test_caller_modified_packet_fails_even_if_witness_matches(tmp_path):
    ledger, retained, steps, packet = _fixture(tmp_path)
    bad = replace(packet, packet_sha256="0" * 64)
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, PLAN, steps, bad)


def test_ledger_callback_retargeting_packet_is_detected(tmp_path, monkeypatch):
    ledger, retained, steps, packet = _fixture(tmp_path)
    original_inspect = DisconnectedWriteSlotLedger.inspect

    def tampered(self, *, retained):
        observed = original_inspect(self, retained=retained)
        object.__setattr__(packet, "packet_sha256", "0" * 64)
        return observed

    monkeypatch.setattr(DisconnectedWriteSlotLedger, "inspect", tampered)
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)


def test_forged_result_authority_is_denied(tmp_path, monkeypatch):
    ledger, retained, steps, packet = _fixture(tmp_path)
    monkeypatch.setattr(
        OfflineWriteTriageRecheck, "replay_authorized",
        property(lambda self: True),
    )
    with pytest.raises(OfflineWriteTriageRecheckRejected, match="authority"):
        recheck_offline_write_triage(ledger, retained, PLAN, steps, packet)


def test_exact_input_types_are_required(tmp_path):
    ledger, retained, steps, packet = _fixture(tmp_path)
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(object(), retained, PLAN, steps, packet)
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, retained, PLAN, list(steps), packet)
