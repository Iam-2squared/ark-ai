"""An inert WRITE recheck must not return after a nested packet item changes."""

from dataclasses import replace

import pytest

from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)
from ark.agency.offline_write_manual_triage import build_offline_write_triage_packet
from ark.agency.offline_write_triage_recheck import (
    OfflineWriteTriageRecheck,
    OfflineWriteTriageRecheckRejected,
    recheck_offline_write_triage,
)

_PLAN = "plan_" + "a" * 64
_STEP = "step_" + "b" * 16


def _fixture(tmp_path):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "write-epoch.db").resolve(), create=True,
    )
    witness = genesis_write_slot_witness()
    steps = (OfflineRecoveryStepClaim(_STEP, "WRITE", (), "UNKNOWN", None),)
    packet = build_offline_write_triage_packet(ledger, witness, _PLAN, steps)
    return ledger, witness, steps, packet


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("step_id", "step_" + "c" * 16),
        ("claimed_state", "PENDING"),
        ("disposition", "WAIT_DEPENDENCY"),
        ("investigation", "CLAIMED_OUTCOME_REVIEW_ONLY"),
        ("reservation_id", "slot_" + "d" * 64),
    ],
)
def test_result_constructor_cannot_mutate_a_nested_item_after_validation(
    tmp_path, monkeypatch, field, changed,
):
    ledger, witness, steps, packet = _fixture(tmp_path)
    original_init = OfflineWriteTriageRecheck.__init__

    def mutate_on_result_creation(self, *args):
        original_init(self, *args)
        # The verifier and rebuilt packet were already compared. Before the
        # fix this mutation escaped the final top-level-only carrier check.
        object.__setattr__(packet.items[0], field, changed)

    monkeypatch.setattr(
        OfflineWriteTriageRecheck, "__init__", mutate_on_result_creation,
    )
    with pytest.raises(
        OfflineWriteTriageRecheckRejected, match="nested triage item changed",
    ):
        recheck_offline_write_triage(ledger, witness, _PLAN, steps, packet)


def test_valid_packet_still_rechecks_without_dispatch(tmp_path):
    ledger, witness, steps, packet = _fixture(tmp_path)
    report = recheck_offline_write_triage(ledger, witness, _PLAN, steps, packet)
    assert report.write_count == 1
    assert report.uncertain_write_count == 1
    assert report.dispatch_authorized is False
    assert report.replay_authorized is False


def test_replaced_nested_item_type_is_denied_at_ingress(tmp_path):
    ledger, witness, steps, packet = _fixture(tmp_path)
    object.__setattr__(packet, "items", (object(),))
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, witness, _PLAN, steps, packet)


def test_replaced_nested_tuple_is_denied_by_packet_verification(tmp_path):
    ledger, witness, steps, packet = _fixture(tmp_path)
    object.__setattr__(
        packet, "items", (replace(packet.items[0], claimed_state="PENDING"),),
    )
    with pytest.raises(OfflineWriteTriageRecheckRejected):
        recheck_offline_write_triage(ledger, witness, _PLAN, steps, packet)
