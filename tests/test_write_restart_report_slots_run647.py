"""Fail closed on forged disconnected WRITE restart result carrier slots.

The review and SQLite ledger are synthetic. A result is never consent,
a trusted clock, tool dispatch authority or permission to replay WRITE.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_write_restart_binding as binding
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "b" * 16


def _case(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "restart-slots.sqlite", create=True)
    retained = genesis_write_slot_witness()
    claim = OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN")
    return ledger, retained, (claim,)


def _review(case):
    ledger, retained, claims = case
    return binding.review_disconnected_write_restart(ledger, retained, PLAN, claims)


@pytest.mark.parametrize(
    "slot", (
        "plan_id", "total_steps", "reserved_write_steps",
        "quarantined_write_steps", "fingerprint",
    ),
)
def test_forged_report_field_denied_before_read(tmp_path, monkeypatch, slot):
    case = _case(tmp_path)
    invoked = []

    def hostile_getter(_self):
        invoked.append(slot)
        raise AssertionError("forged report getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            binding.OfflineWriteRestartReport,
            slot,
            property(hostile_getter),
        )
        patch.setattr(
            case[0], "_open",
            lambda **_kwargs: pytest.fail("ledger opened before slot preflight"),
        )
        with pytest.raises(
            binding.OfflineWriteRestartRejected, match="constructor changed",
        ):
            _review(case)
    assert invoked == []
    assert case[0].inspect(retained=case[1]) == case[1]


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_forged_report_lookup_denied_before_read(tmp_path, monkeypatch, hook):
    case = _case(tmp_path)
    invoked = []

    def hostile_lookup(_self, _name):
        invoked.append(hook)
        raise AssertionError("forged report lookup executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            binding.OfflineWriteRestartReport,
            hook,
            hostile_lookup,
            raising=False,
        )
        patch.setattr(
            case[0], "_open",
            lambda **_kwargs: pytest.fail("ledger opened before hook preflight"),
        )
        with pytest.raises(
            binding.OfflineWriteRestartRejected, match="constructor changed",
        ):
            _review(case)
    assert invoked == []
    assert case[0].inspect(retained=case[1]) == case[1]


def test_reentrant_quarantine_callback_cannot_replace_result_slot(
    tmp_path, monkeypatch,
):
    case = _case(tmp_path)
    original = binding.review_disconnected_recovery_fence
    invoked = []

    def hostile_getter(_self):
        invoked.append("fingerprint")
        raise AssertionError("forged result slot executed")

    def inject(*args):
        result = original(*args)
        monkeypatch.setattr(
            binding.OfflineWriteRestartReport,
            "fingerprint",
            property(hostile_getter),
        )
        return result

    with monkeypatch.context() as patch:
        patch.setattr(binding, "review_disconnected_recovery_fence", inject)
        with pytest.raises(
            binding.OfflineWriteRestartRejected, match="constructor changed",
        ):
            _review(case)
    assert invoked == []
    assert case[0].inspect(retained=case[1]) == case[1]


def test_original_unknown_write_still_requires_manual_triage(tmp_path):
    case = _case(tmp_path)
    result = _review(case)
    assert result.quarantined_write_steps == 1
    assert result.reserved_write_steps == 0
    assert result.write_replay_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.cross_store_atomicity_proven is False
