"""Synthetic recovery must reject substituted constructor callbacks.

No tool is dispatched; UNKNOWN WRITE is quarantined and READ is mock-only.
"""
from __future__ import annotations

import pytest

import ark.agency.disconnected_write_recovery_fence as mod

PLAN = "plan_" + "a" * 64
WRITE = "step_" + "1" * 16
READ = "step_" + "2" * 16


def _review():
    return mod.review_disconnected_recovery_fence(
        PLAN, (
            mod.OfflineRecoveryStepClaim(WRITE, "WRITE", (), "UNKNOWN"),
            mod.OfflineRecoveryStepClaim(READ, "READ", (WRITE,), "PENDING"),
        ),
    )


@pytest.mark.parametrize("kind", ("disposition", "fence"))
@pytest.mark.parametrize("mode", ("global_name", "actual_init"))
def test_substituted_constructor_rejected_before_call(monkeypatch, kind, mode):
    called = []
    cls = (
        mod.OfflineRecoveryDisposition if kind == "disposition"
        else mod.OfflineRecoveryFence
    )

    def callback(*args):
        called.append(args)

    if mode == "global_name":
        name = (
            "OfflineRecoveryDisposition" if kind == "disposition"
            else "OfflineRecoveryFence"
        )
        monkeypatch.setattr(mod, name, callback)
    else:
        monkeypatch.setattr(cls, "__init__", callback)

    with pytest.raises(
        mod.OfflineRecoveryFenceRejected, match="authority descriptor changed",
    ):
        _review()
    assert called == []


@pytest.mark.parametrize("kind", ("disposition", "fence"))
def test_constructor_rebound_in_hash_callback_rejected(monkeypatch, kind):
    called = []
    name = (
        "OfflineRecoveryDisposition" if kind == "disposition"
        else "OfflineRecoveryFence"
    )
    prior = mod.hashlib.sha256
    hash_callback_calls = []

    def constructor(*args):
        called.append(args)

    def replace_on_hash(payload):
        hash_callback_calls.append(payload)
        monkeypatch.setattr(mod, name, constructor)
        return prior(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", replace_on_hash)
    with pytest.raises(
        mod.OfflineRecoveryFenceRejected,
        match="mixed-plan digest implementation or domain changed",
    ):
        _review()
    assert called == []
    assert hash_callback_calls == []


def test_clean_unknown_write_remains_held_and_read_not_dispatched():
    result = _review()
    assert tuple(v.code for v in result.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.write_authorized is False
    assert result.external_outcome_verified is False
