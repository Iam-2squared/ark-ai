"""Disconnected UNKNOWN WRITE triage cannot mint any execution authority."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_write_recovery_fence as mod

PLAN = "plan_" + "a" * 64
WRITE = "step_" + "1" * 16
DEPENDENT = "step_" + "2" * 16


def _claim():
    return (
        mod.OfflineRecoveryStepClaim(WRITE, "WRITE", (), "UNKNOWN"),
        mod.OfflineRecoveryStepClaim(DEPENDENT, "READ", (WRITE,), "PENDING"),
    )


@pytest.mark.parametrize("field", (
    "dispatch_authorized",
    "automatic_replay_authorized",
    "write_authorized",
    "external_outcome_verified",
))
def test_forged_authority_on_result_is_rejected(monkeypatch, field):
    monkeypatch.setattr(
        mod.OfflineRecoveryFence, field, property(lambda _receipt: True),
    )
    with pytest.raises(mod.OfflineRecoveryFenceRejected, match="result carrier"):
        mod.review_disconnected_recovery_fence(PLAN, _claim())


def test_constructor_time_authority_injection_is_rejected(monkeypatch):
    original = mod.OfflineRecoveryFence

    def forged(plan_id, decisions, digest):
        result = original(plan_id, decisions, digest)
        monkeypatch.setattr(
            original, "automatic_replay_authorized",
            property(lambda _receipt: True),
        )
        return result

    monkeypatch.setattr(mod, "OfflineRecoveryFence", forged)
    with pytest.raises(mod.OfflineRecoveryFenceRejected, match="result carrier"):
        mod.review_disconnected_recovery_fence(PLAN, _claim())


def test_normal_unknown_write_remains_quarantined_and_denied():
    report = mod.review_disconnected_recovery_fence(PLAN, _claim())
    assert tuple(item.code for item in report.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.write_authorized is False
    assert report.external_outcome_verified is False
