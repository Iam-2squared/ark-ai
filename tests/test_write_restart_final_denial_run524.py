"""UNKNOWN WRITE restart remains quarantined after final synthetic callbacks.

The local SQLite slot journal is not an external outcome, consent or trusted clock.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_restart_binding import (
    OfflineWriteRestartRejected,
    OfflineWriteRestartReport,
    review_disconnected_write_restart,
)
from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerRejected,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "b" * 16
REQUEST = "c" * 64


def setup_case(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "write-slots.sqlite", create=True)
    retained = genesis_write_slot_witness()
    claims = (OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN"),)
    return ledger, retained, claims


def review(case):
    ledger, retained, claims = case
    return review_disconnected_write_restart(ledger, retained, PLAN, claims)


def test_unknown_unreserved_write_never_acquires_replay_authority(tmp_path):
    case = setup_case(tmp_path)
    result = review(case)
    assert type(result) is OfflineWriteRestartReport
    assert result.total_steps == 1
    assert result.quarantined_write_steps == 1
    assert result.reserved_write_steps == 0
    assert result.tool_dispatch_authorized is False
    assert result.write_replay_authorized is False
    assert result.external_outcome_verified is False
    assert result.trusted_clock_verified is False
    assert result.consent_verified is False
    assert result.cross_store_atomicity_proven is False


@pytest.mark.parametrize("field, forged", [
    ("fingerprint", "f" * 64),
    ("plan_id", "plan_" + "f" * 64),
    ("quarantined_write_steps", 0),
])
def test_last_false_authority_getter_cannot_mutate_report(
    tmp_path, monkeypatch, field, forged,
):
    case = setup_case(tmp_path)

    def malicious_false(self):
        object.__setattr__(self, field, forged)
        return False

    monkeypatch.setattr(
        OfflineWriteRestartReport, "cross_store_atomicity_proven",
        property(malicious_false),
    )
    with pytest.raises(OfflineWriteRestartRejected, match="report changed"):
        review(case)


@pytest.mark.parametrize("forged", [True, 1])
def test_exact_false_required_for_write_replay_authority(
    tmp_path, monkeypatch, forged,
):
    case = setup_case(tmp_path)
    monkeypatch.setattr(
        OfflineWriteRestartReport, "write_replay_authorized",
        property(lambda self: forged),
    )
    with pytest.raises(OfflineWriteRestartRejected, match="acquired authority"):
        review(case)


def test_last_false_getter_cannot_append_undetected_durable_write_slot(
    tmp_path, monkeypatch,
):
    case = setup_case(tmp_path)
    ledger, retained, _ = case
    slot = derive_disconnected_write_slot_id(PLAN, STEP, REQUEST)
    claim = DetachedWriteSlotClaim(slot, PLAN, STEP, REQUEST)

    def malicious_false(self):
        ledger.reserve_many((claim,), retained=retained)
        return False

    monkeypatch.setattr(
        OfflineWriteRestartReport, "cross_store_atomicity_proven",
        property(malicious_false),
    )
    with pytest.raises(
        OfflineWriteRestartRejected, match="ledger changed after final authority denial",
    ):
        review(case)
    # Even the test's synthetic reserve is not permission to dispatch/replay.
    with pytest.raises(WriteSlotLedgerRejected, match="stale or changed retained history"):
        ledger.inspect(retained=retained)
