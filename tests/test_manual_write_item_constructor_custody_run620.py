"""Manual-only WRITE triage never executes a substituted item constructor.

All data is synthetic and local. No backend operation, consent, review decision,
notification, external outcome verification or automatic replay is granted.
"""

import pytest

from ark.agency import offline_write_manual_triage as triage
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

_PLAN = "plan_" + "a" * 64
_STEP = "step_" + "1" * 16


def _inputs(tmp_path, effect):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "manual-only.sqlite").resolve(), create=True,
    )
    step = OfflineRecoveryStepClaim(
        _STEP, effect, (), "UNKNOWN" if effect == "WRITE" else "PENDING",
    )
    return ledger, genesis_write_slot_witness(), _PLAN, (step,)


@pytest.mark.parametrize("effect", ("READ", "WRITE"))
def test_preinstalled_item_constructor_rejected_before_child_review(
    tmp_path, monkeypatch, effect,
):
    inputs = _inputs(tmp_path, effect)
    calls = []

    def counterfeit(*_args, **_kwargs):
        calls.append("constructor invoked")
        raise AssertionError("forged item constructor must not execute")

    def child_called(*_args, **_kwargs):
        raise AssertionError("child review must not run with forged item constructor")

    with monkeypatch.context() as patch:
        patch.setattr(triage.OfflineWriteTriageItem, "__init__", counterfeit)
        patch.setattr(triage, "review_disconnected_write_restart", child_called)
        with pytest.raises(triage.OfflineWriteTriageRejected, match="descriptor changed"):
            triage.build_offline_write_triage_packet(*inputs)

    assert calls == []


@pytest.mark.parametrize("effect", ("READ", "WRITE"))
def test_reentrant_child_cannot_install_item_constructor(
    tmp_path, monkeypatch, effect,
):
    inputs = _inputs(tmp_path, effect)
    original = triage.review_disconnected_recovery_fence
    calls = []

    def counterfeit(*_args, **_kwargs):
        calls.append("constructor invoked")
        raise AssertionError("forged item constructor must not execute")

    with monkeypatch.context() as patch:
        def child_hook(*args, **kwargs):
            result = original(*args, **kwargs)
            patch.setattr(triage.OfflineWriteTriageItem, "__init__", counterfeit)
            return result

        patch.setattr(triage, "review_disconnected_recovery_fence", child_hook)
        # Child validation wraps local pre-getter refusal without relaxing
        # the no-constructor and no-replay invariants.
        with pytest.raises(
            triage.OfflineWriteTriageRejected,
            match="local WRITE recovery validation denied",
        ):
            triage.build_offline_write_triage_packet(*inputs)

    assert calls == []


def test_original_item_constructor_keeps_unknown_write_quarantined(tmp_path):
    packet = triage.build_offline_write_triage_packet(*_inputs(tmp_path, "WRITE"))
    assert len(packet.items) == 1
    assert packet.items[0].investigation == "UNKNOWN_EFFECT_HOLD"
    assert packet.human_review_completed is False
    assert packet.external_outcome_verified is False
    assert packet.dispatch_authorized is False
    assert packet.automatic_replay_authorized is False
