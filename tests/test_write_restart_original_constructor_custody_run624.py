"""Disconnected WRITE restart report construction never grants replay or dispatch."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_write_restart_binding as restart
from ark.agency.disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from ark.agency.disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    genesis_write_slot_witness,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "b" * 16


def _case(tmp_path):
    ledger = DisconnectedWriteSlotLedger(tmp_path / "no-external-write.sqlite", create=True)
    retained = genesis_write_slot_witness()
    claim = OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN")
    return ledger, retained, (claim,)


def _review(case):
    ledger, retained, steps = case
    return restart.review_disconnected_write_restart(ledger, retained, PLAN, steps)


def test_preinstalled_constructor_refused_before_ledger_read(tmp_path, monkeypatch):
    case = _case(tmp_path)
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("hostile WRITE report constructor executed")

    with monkeypatch.context() as patch:
        patch.setattr(restart.OfflineWriteRestartReport, "__init__", hostile)
        patch.setattr(
            case[0], "_open",
            lambda **_kwargs: pytest.fail("SQLite opened before constructor veto"),
        )
        with pytest.raises(restart.OfflineWriteRestartRejected, match="constructor changed"):
            _review(case)
    assert invoked == []


def test_constructor_mutation_during_quarantine_callback_rejected(
    tmp_path, monkeypatch,
):
    case = _case(tmp_path)
    invoked = []
    original = restart.review_disconnected_recovery_fence

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("hostile WRITE constructor executed")

    def mutate(*args):
        result = original(*args)
        monkeypatch.setattr(restart.OfflineWriteRestartReport, "__init__", hostile)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(restart, "review_disconnected_recovery_fence", mutate)
        with pytest.raises(restart.OfflineWriteRestartRejected, match="constructor changed"):
            _review(case)
    assert invoked == []
    assert case[0].inspect(retained=case[1]) == case[1]


def test_constructor_mutation_after_first_ledger_scan_rejected(
    tmp_path, monkeypatch,
):
    case = _case(tmp_path)
    original = restart._inspect
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("substituted initializer executed")

    def mutate(conn):
        result = original(conn)
        monkeypatch.setattr(restart.OfflineWriteRestartReport, "__init__", hostile)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(restart, "_inspect", mutate)
        with pytest.raises(restart.OfflineWriteRestartRejected, match="constructor changed"):
            _review(case)
    assert invoked == []


def test_exact_unknown_write_report_stays_manual_only(tmp_path):
    case = _case(tmp_path)
    report = _review(case)
    assert type(report) is restart.OfflineWriteRestartReport
    assert report.quarantined_write_steps == 1
    assert report.reserved_write_steps == 0
    assert report.tool_dispatch_authorized is False
    assert report.write_replay_authorized is False
    assert report.external_outcome_verified is False
    assert report.trusted_clock_verified is False
    assert report.consent_verified is False
    assert report.cross_store_atomicity_proven is False
