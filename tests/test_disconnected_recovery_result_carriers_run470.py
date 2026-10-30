"""Disconnected mixed-plan recovery result carriers never imply WRITE authority."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.agency import disconnected_write_recovery_fence as module

PLAN = "plan_" + "a" * 64
A = "step_" + "1" * 16
B = "step_" + "2" * 16


def _steps():
    return (
        module.OfflineRecoveryStepClaim(A, "WRITE", (), "UNKNOWN"),
        module.OfflineRecoveryStepClaim(B, "READ", (A,), "PENDING"),
    )


def test_original_recovery_result_remains_deny_only():
    receipt = module.review_disconnected_recovery_fence(PLAN, _steps())
    assert tuple(x.code for x in receipt.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.write_authorized is False


def test_forged_disposition_factory_is_rejected(monkeypatch):
    def forge(name, code):
        return SimpleNamespace(step_id=name, code=code, dispatch_authorized=True)

    monkeypatch.setattr(module, "OfflineRecoveryDisposition", forge)
    with pytest.raises(module.OfflineRecoveryFenceRejected, match="disposition carrier"):
        module.review_disconnected_recovery_fence(PLAN, _steps())


def test_earlier_disposition_reflective_mutation_is_rejected(monkeypatch):
    original = module.OfflineRecoveryDisposition
    results = []

    def mutate_before_second(name, code):
        if results:
            object.__setattr__(results[0], "code", "READY_MOCK_ONLY")
        item = original(name, code)
        results.append(item)
        return item

    monkeypatch.setattr(module, "OfflineRecoveryDisposition", mutate_before_second)
    with pytest.raises(module.OfflineRecoveryFenceRejected, match="disposition changed"):
        module.review_disconnected_recovery_fence(PLAN, _steps())


def test_disposition_mutation_during_digest_is_rejected(monkeypatch):
    original_factory = module.OfflineRecoveryDisposition
    original_hash = module.hashlib.sha256
    results = []

    def collect(name, code):
        item = original_factory(name, code)
        results.append(item)
        return item

    def mutate_during_hash(payload):
        object.__setattr__(results[0], "code", "READY_MOCK_ONLY")
        return original_hash(payload)

    monkeypatch.setattr(module, "OfflineRecoveryDisposition", collect)
    monkeypatch.setattr(module.hashlib, "sha256", mutate_during_hash)
    with pytest.raises(module.OfflineRecoveryFenceRejected, match="disposition changed"):
        module.review_disconnected_recovery_fence(PLAN, _steps())


def test_forged_review_factory_is_rejected(monkeypatch):
    def forge(plan_id, decisions, digest):
        return SimpleNamespace(
            plan_id=plan_id, decisions=decisions, digest=digest,
            dispatch_authorized=True,
        )

    monkeypatch.setattr(module, "OfflineRecoveryFence", forge)
    with pytest.raises(module.OfflineRecoveryFenceRejected, match="result carrier"):
        module.review_disconnected_recovery_fence(PLAN, _steps())


def test_review_constructor_cannot_rewrite_nested_dispositions(monkeypatch):
    original = module.OfflineRecoveryFence

    def mutate_before_return(plan_id, decisions, digest):
        object.__setattr__(decisions[0], "code", "READY_MOCK_ONLY")
        return original(plan_id, decisions, digest)

    monkeypatch.setattr(module, "OfflineRecoveryFence", mutate_before_return)
    with pytest.raises(module.OfflineRecoveryFenceRejected, match="disposition changed"):
        module.review_disconnected_recovery_fence(PLAN, _steps())
