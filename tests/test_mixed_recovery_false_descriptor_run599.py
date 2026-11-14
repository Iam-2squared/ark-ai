"""A synthetic recovery receipt cannot replace its deny-only getters.

These claims are detached diagnostics. They never provide permissions to
restart a RUNNING/UNKNOWN WRITE or to execute a backend.
"""

import pytest

import ark.agency.disconnected_write_recovery_fence as mod

PLAN = "plan_" + "a" * 64
WRITE = "step_" + "1" * 16
CHILD = "step_" + "2" * 16
READ = "step_" + "3" * 16


def _claims():
    return (
        mod.OfflineRecoveryStepClaim(WRITE, "WRITE", (), "UNKNOWN"),
        mod.OfflineRecoveryStepClaim(CHILD, "READ", (WRITE,), "PENDING"),
        mod.OfflineRecoveryStepClaim(READ, "READ", (), "PENDING"),
    )


@pytest.mark.parametrize("field", (
    "dispatch_authorized", "automatic_replay_authorized",
    "write_authorized", "external_outcome_verified",
))
def test_false_looking_substituted_authority_is_rejected(monkeypatch, field):
    monkeypatch.setattr(mod.OfflineRecoveryFence, field, property(lambda _: False))
    with pytest.raises(
        mod.OfflineRecoveryFenceRejected, match="authority descriptor changed",
    ):
        mod.review_disconnected_recovery_fence(PLAN, _claims())


def test_digest_callback_cannot_install_late_false_descriptor(monkeypatch):
    original_digest = mod.hashlib.sha256
    callback_calls = []

    def spoof_after_digest(payload):
        callback_calls.append(payload)
        monkeypatch.setattr(
            mod.OfflineRecoveryFence,
            "automatic_replay_authorized", property(lambda _: False),
        )
        return original_digest(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", spoof_after_digest)
    with pytest.raises(
        mod.OfflineRecoveryFenceRejected,
        match="mixed-plan digest implementation or domain changed",
    ):
        mod.review_disconnected_recovery_fence(PLAN, _claims())
    assert callback_calls == []


def test_mixed_unknown_write_keeps_quarantine_and_independent_read():
    receipt = mod.review_disconnected_recovery_fence(PLAN, _claims())
    assert tuple(entry.code for entry in receipt.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN", "READY_MOCK_ONLY",
    )
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.write_authorized is False
    assert receipt.external_outcome_verified is False
