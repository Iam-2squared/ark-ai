"""Disconnected mixed-plan restart review rejects truncated policy vectors.

No real execution or WRITE replay occurs. All outcome claims are synthetic.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_write_recovery_fence as recovery

_PLAN = "plan_" + "a" * 64
_WRITE = "step_" + "1" * 16
_READ = "step_" + "2" * 16


def _claims():
    return (
        recovery.OfflineRecoveryStepClaim(_WRITE, "WRITE", (), "UNKNOWN"),
        recovery.OfflineRecoveryStepClaim(_READ, "READ", (_WRITE,), "PENDING"),
    )


@pytest.mark.parametrize("vector", (
    "_STEP_MEMBERS", "_DISPOSITION_MEMBERS", "_FENCE_MEMBERS",
    "_FENCE_DENIAL_NAMES",
))
@pytest.mark.parametrize("mutation", ("empty", "reversed", "equal_rebound"))
def test_recovery_policy_vector_swap_rejected_before_claim_access(
    monkeypatch, vector, mutation,
):
    previous = getattr(recovery, vector)
    assert len(previous) > 1
    if mutation == "empty":
        replacement = ()
    elif mutation == "reversed":
        replacement = tuple(reversed(previous))
    else:
        replacement = tuple(list(previous))
        assert replacement == previous and replacement is not previous

    monkeypatch.setattr(recovery, vector, replacement)
    with pytest.raises(
        recovery.OfflineRecoveryFenceRejected, match="policy vector changed",
    ):
        recovery.review_disconnected_recovery_fence(_PLAN, _claims())


def test_shortened_denial_vector_cannot_hide_forged_replay_getter(monkeypatch):
    called = []

    def forged(self):
        called.append(True)
        return False

    monkeypatch.setattr(recovery, "_FENCE_DENIAL_NAMES", ())
    monkeypatch.setattr(
        recovery.OfflineRecoveryFence, "automatic_replay_authorized",
        property(forged),
    )
    with pytest.raises(
        recovery.OfflineRecoveryFenceRejected, match="policy vector changed",
    ):
        recovery.review_disconnected_recovery_fence(_PLAN, _claims())
    assert called == []


def test_shortened_step_hooks_cannot_trigger_private_claim_getter(monkeypatch):
    called = []

    def forged(self, name):
        called.append(name)
        raise AssertionError("unreviewed recovery claim getter executed")

    monkeypatch.setattr(recovery, "_STEP_MEMBERS", ())
    monkeypatch.setattr(
        recovery.OfflineRecoveryStepClaim, "__getattribute__", forged,
    )
    with pytest.raises(
        recovery.OfflineRecoveryFenceRejected, match="policy vector changed",
    ):
        recovery.review_disconnected_recovery_fence(_PLAN, _claims())
    assert called == []


def test_clean_unknown_write_remains_quarantined_and_read_not_dispatched():
    result = recovery.review_disconnected_recovery_fence(_PLAN, _claims())
    assert tuple(row.code for row in result.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.write_authorized is False
    assert result.external_outcome_verified is False
