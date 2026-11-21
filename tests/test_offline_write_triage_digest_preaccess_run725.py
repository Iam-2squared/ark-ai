"""Manual-only WRITE triage rejects hostile digest callbacks before private inputs.

These assertions certify only local fail-closed behavior, never human review,
external effect, permission or automatic uncertain-effect retry.
"""

from __future__ import annotations

import pytest

from ark.agency import offline_write_manual_triage as triage
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "1" * 16


def _case(tmp_path):
    ledger = DisconnectedWriteSlotLedger(
        (tmp_path / "write-slots.sqlite").resolve(), create=True,
    )
    retained = genesis_write_slot_witness()
    steps = (OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN", None),)
    return ledger, retained, steps


@pytest.mark.parametrize("component", ("sha256", "json", "domain"))
def test_replaced_digest_primitive_refused_before_private_step_access(
    tmp_path, monkeypatch, component,
):
    ledger, retained, steps = _case(tmp_path)
    calls = []

    def hostile(*args, **kwargs):
        calls.append("exposed")
        raise AssertionError("private evidence was passed to untrusted callback")

    with monkeypatch.context() as patch:
        # An early refusal must not inspect even the ordinary step fields.
        def unsafe_step_getattribute(self, name):
            calls.append(("step", name))
            raise AssertionError("private step fields accessed before refusing callback")

        patch.setattr(triage._STEP_TYPE, "__getattribute__", unsafe_step_getattribute)
        if component == "sha256":
            patch.setattr(triage.hashlib, "sha256", hostile)
        elif component == "json":
            patch.setattr(triage.json, "dumps", hostile)
        else:
            patch.setattr(triage, "_DOMAIN", b"changed-domain")
        with pytest.raises(
            triage.OfflineWriteTriageRejected,
            match="authority descriptor changed",
        ):
            triage.build_offline_write_triage_packet(
                ledger, retained, PLAN, steps,
            )
        assert calls == []
    # Original fixture is still harmless when the synthetic substitutions end.
    report = triage.build_offline_write_triage_packet(ledger, retained, PLAN, steps)
    assert report.automatic_replay_authorized is False
    assert report.dispatch_authorized is False


@pytest.mark.parametrize("component", ("sha256", "json", "domain"))
def test_digest_dependency_change_during_child_review_denied(
    tmp_path, monkeypatch, component,
):
    ledger, retained, steps = _case(tmp_path)
    original = triage.review_disconnected_write_restart
    hostile_calls = []

    def hostile(*args, **kwargs):
        hostile_calls.append("leak")
        raise AssertionError("injected digest callback executed")

    with monkeypatch.context() as patch:
        # Use the same test-local patch context for child rebinding so that
        # no concurrent sibling test or fixture retains a modified global.
        def changed_child_scoped(*args, **kwargs):
            result = original(*args, **kwargs)
            if component == "sha256":
                patch.setattr(triage.hashlib, "sha256", hostile)
            elif component == "json":
                patch.setattr(triage.json, "dumps", hostile)
            else:
                patch.setattr(triage, "_DOMAIN", b"changed-domain")
            return result

        patch.setattr(triage, "review_disconnected_write_restart", changed_child_scoped)
        with pytest.raises(
            triage.OfflineWriteTriageRejected,
            match="local WRITE recovery validation denied",
        ):
            triage.build_offline_write_triage_packet(ledger, retained, PLAN, steps)
    assert hostile_calls == []
