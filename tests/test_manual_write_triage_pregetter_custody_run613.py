"""Offline WRITE triage never executes forged denial properties.

Disposable local SQLite reservations only; no external WRITE, consent,
human decision, dispatch or replay is authorized by any generated packet.
"""

import pytest

from ark.agency import offline_write_manual_triage as triage
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "1" * 16


class ExecutableFalse:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("forged getter invoked")
        return False


def _inputs(tmp_path, *, effect="WRITE"):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "manual-triage.sqlite").resolve(), create=True,
    )
    witness = genesis_write_slot_witness()
    steps = (OfflineRecoveryStepClaim(
        STEP, effect, (), "UNKNOWN" if effect == "WRITE" else "PENDING",
    ),)
    return ledger, witness, PLAN, steps


@pytest.mark.parametrize(
    ("carrier", "flag"),
    [
        ("packet", flag) for flag in triage._PACKET_DENIALS
    ] + [
        ("restart", flag) for flag in triage._RESTART_DENIALS
    ] + [
        ("fence", flag) for flag in triage._FENCE_DENIALS
    ],
)
def test_counterfeit_false_denial_never_invoked(
    tmp_path, monkeypatch, carrier, flag,
):
    ledger, retained, plan, steps = _inputs(tmp_path)
    classes = {
        "packet": triage._PACKET_TYPE,
        "restart": triage._RESTART_TYPE,
        "fence": triage._FENCE_TYPE,
    }
    calls = []
    monkeypatch.setattr(classes[carrier], flag, ExecutableFalse(calls))
    with pytest.raises(triage.OfflineWriteTriageRejected, match="descriptor changed"):
        triage.build_offline_write_triage_packet(ledger, retained, plan, steps)
    assert calls == []


@pytest.mark.parametrize("flag", triage._PACKET_DENIALS)
def test_constructor_injected_false_denial_rejected_before_getter(
    tmp_path, monkeypatch, flag,
):
    ledger, retained, plan, steps = _inputs(tmp_path)
    calls = []
    cls = triage._PACKET_TYPE
    initial = vars(cls)[flag]
    original_init = cls.__init__
    constructor_calls = []

    def injected_init(self, *args, **kwargs):
        constructor_calls.append("counterfeit packet initializer executed")
        original_init(self, *args, **kwargs)
        monkeypatch.setattr(cls, flag, ExecutableFalse(calls))

    monkeypatch.setattr(cls, "__init__", injected_init)
    with pytest.raises(triage.OfflineWriteTriageRejected, match="descriptor changed"):
        triage.build_offline_write_triage_packet(ledger, retained, plan, steps)
    assert calls == []
    # The substituted initializer itself is now rejected before execution.
    assert constructor_calls == []
    assert vars(cls)[flag] is initial


@pytest.mark.parametrize("effect", ("READ", "WRITE"))
def test_ordinary_manual_packet_remains_inert(tmp_path, effect):
    packet = triage.build_offline_write_triage_packet(
        *_inputs(tmp_path, effect=effect),
    )
    assert len(packet.items) == (0 if effect == "READ" else 1)
    assert packet.human_review_completed is False
    assert packet.external_outcome_verified is False
    assert packet.dispatch_authorized is False
    assert packet.automatic_replay_authorized is False
    if packet.items:
        assert packet.items[0].investigation == "UNKNOWN_EFFECT_HOLD"
