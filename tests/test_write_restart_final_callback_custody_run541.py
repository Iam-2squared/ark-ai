"""Final restart callbacks must not change denied authority or Planner recovery.

All claims and SQLite reservations here are synthetic. Nothing dispatches,
authorizes a WRITE retry, proves a real outcome, or authenticates a clock.
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
    ledger = DisconnectedWriteSlotLedger(tmp_path / "restart-final.sqlite", create=True)
    retained = genesis_write_slot_witness()
    step = OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN")
    return ledger, retained, step


@pytest.mark.parametrize("first,last", (
    ("tool_dispatch_authorized", "write_replay_authorized"),
    ("consent_verified", "cross_store_atomicity_proven"),
))
def test_false_getter_cannot_rebind_another_denial(
    tmp_path, monkeypatch, first, last,
):
    ledger, retained, step = _case(tmp_path)

    def rebind(self):
        monkeypatch.setattr(
            binding.OfflineWriteRestartReport, last, property(lambda self: False),
        )
        return False

    monkeypatch.setattr(
        binding.OfflineWriteRestartReport, first, property(rebind),
    )
    with pytest.raises(binding.OfflineWriteRestartRejected, match="report changed"):
        binding.review_disconnected_write_restart(ledger, retained, PLAN, (step,))
    assert ledger.inspect(retained=retained) == retained


def test_last_false_getter_cannot_replace_its_own_descriptor(tmp_path, monkeypatch):
    ledger, retained, step = _case(tmp_path)

    def replace_self(self):
        monkeypatch.setattr(
            binding.OfflineWriteRestartReport,
            "cross_store_atomicity_proven",
            property(lambda self: False),
        )
        return False

    monkeypatch.setattr(
        binding.OfflineWriteRestartReport,
        "cross_store_atomicity_proven",
        property(replace_self),
    )
    with pytest.raises(binding.OfflineWriteRestartRejected, match="report changed"):
        binding.review_disconnected_write_restart(ledger, retained, PLAN, (step,))
    assert ledger.inspect(retained=retained) == retained


@pytest.mark.parametrize("target", ("step", "fence"))
def test_final_sqlite_callback_cannot_change_previous_recovery_epoch(
    tmp_path, monkeypatch, target,
):
    ledger, retained, step = _case(tmp_path)
    original_inspect = binding._inspect
    original_fence = binding.review_disconnected_recovery_fence
    state = {"reads": 0}
    fence_holder = {}

    def capture(*args):
        result = original_fence(*args)
        fence_holder["result"] = result
        return result

    def mutate_on_final(conn):
        state["reads"] += 1
        observed = original_inspect(conn)
        if state["reads"] == 4:
            if target == "step":
                object.__setattr__(step, "state", "PENDING")
            else:
                object.__setattr__(
                    fence_holder["result"].decisions[0],
                    "code", "READY_MOCK_ONLY",
                )
        return observed

    monkeypatch.setattr(binding, "review_disconnected_recovery_fence", capture)
    monkeypatch.setattr(binding, "_inspect", mutate_on_final)
    expected = "step changed" if target == "step" else "quarantine changed"
    with pytest.raises(binding.OfflineWriteRestartRejected, match=expected):
        binding.review_disconnected_write_restart(ledger, retained, PLAN, (step,))
    assert state["reads"] == 4
    assert ledger.inspect(retained=retained) == retained


def test_original_unknown_write_stays_denied_with_new_final_guards(tmp_path):
    ledger, retained, step = _case(tmp_path)
    report = binding.review_disconnected_write_restart(
        ledger, retained, PLAN, (step,),
    )
    assert report.quarantined_write_steps == 1
    assert report.reserved_write_steps == 0
    assert report.write_replay_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.cross_store_atomicity_proven is False
    assert ledger.inspect(retained=retained) == retained
