"""Replaced final-denial properties cannot authenticate a WRITE restart."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_write_restart_binding as binding
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

_DENIALS = (
    "tool_dispatch_authorized", "write_replay_authorized",
    "external_outcome_verified", "trusted_clock_verified",
    "consent_verified", "cross_store_atomicity_proven",
)


def _setup(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "write_slots.sqlite3", create=True)
    retained = genesis_write_slot_witness()
    plan = "plan_" + "a" * 64
    claim = OfflineRecoveryStepClaim("step_" + "1" * 16, "WRITE", (), "UNKNOWN")
    return ledger, retained, plan, (claim,)


@pytest.mark.parametrize("denial", _DENIALS)
@pytest.mark.parametrize("fake_value", (False, True))
def test_replaced_denial_property_refused_after_final_review(
    tmp_path, monkeypatch, denial, fake_value,
):
    ledger, retained, plan, steps = _setup(tmp_path)
    executed = []

    def injected(self):
        executed.append(denial)
        return fake_value

    with monkeypatch.context() as patch:
        patch.setattr(
            binding.OfflineWriteRestartReport, denial, property(injected),
        )
        reason = (
            "acquired authority" if fake_value is True
            else "denial descriptor changed after review"
        )
        with pytest.raises(binding.OfflineWriteRestartRejected, match=reason):
            binding.review_disconnected_write_restart(
                ledger, retained, plan, steps,
            )
    # The established final-denial regression suite intentionally exercises
    # reentrant getter callbacks; the report can never authorize dispatch.
    assert executed == [denial]
    assert ledger.inspect(retained=retained) == retained


def test_original_unknown_write_remains_quarantined(tmp_path):
    ledger, retained, plan, steps = _setup(tmp_path)
    report = binding.review_disconnected_write_restart(
        ledger, retained, plan, steps,
    )
    assert report.quarantined_write_steps == 1
    assert report.reserved_write_steps == 0
    assert all(getattr(report, name) is False for name in _DENIALS)
    assert ledger.inspect(retained=retained) == retained
