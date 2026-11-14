"""Manual WRITE operator packets never invoke a substituted initializer.

Synthetic SQLite reservations are local-only. Neither a report nor a negative
authority flag authorizes external dispatch, approval, or automatic WRITE replay.
"""

from types import SimpleNamespace

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
        (tmp_path / "manual-packet-custody.sqlite").resolve(), create=True,
    )
    step = OfflineRecoveryStepClaim(
        _STEP, effect, (), "UNKNOWN" if effect == "WRITE" else "PENDING",
    )
    return ledger, genesis_write_slot_witness(), _PLAN, (step,)


@pytest.mark.parametrize("effect", ("READ", "WRITE"))
@pytest.mark.parametrize("injection", ("preinstalled", "fingerprint"))
def test_counterfeit_packet_initializer_never_executes(
    tmp_path, monkeypatch, effect, injection,
):
    inputs = _inputs(tmp_path, effect)
    attempted = []
    original_sha256 = triage.hashlib.sha256
    callbacks = []

    def forbidden(*_args, **_kwargs):
        attempted.append("counterfeit packet initializer executed")
        raise AssertionError("counterfeit initializer must not execute")

    with monkeypatch.context() as patch:
        if injection == "preinstalled":
            patch.setattr(triage._PACKET_TYPE, "__init__", forbidden)
        else:
            def fingerprint_callback(payload=b""):
                if payload.startswith(triage._DOMAIN):
                    callbacks.append("operator packet digest")
                    patch.setattr(triage._PACKET_TYPE, "__init__", forbidden)
                return original_sha256(payload)

            patch.setattr(
                triage, "hashlib", SimpleNamespace(sha256=fingerprint_callback),
            )

        with pytest.raises(
            triage.OfflineWriteTriageRejected,
            match="authority descriptor changed",
        ):
            triage.build_offline_write_triage_packet(*inputs)

    assert attempted == []
    if injection == "fingerprint":
        # The earlier digest-implementation fence denies the substitute
        # before it can read or hash the operator packet.
        assert callbacks == []


@pytest.mark.parametrize("effect", ("READ", "WRITE"))
def test_original_operator_packet_has_no_external_authority(tmp_path, effect):
    packet = triage.build_offline_write_triage_packet(
        *_inputs(tmp_path, effect),
    )
    assert len(packet.items) == (0 if effect == "READ" else 1)
    assert packet.human_review_completed is False
    assert packet.external_outcome_verified is False
    assert packet.dispatch_authorized is False
    assert packet.automatic_replay_authorized is False
