"""Offline quarantine rejects executable input carriers before SQLite access.

Only disposable schedule and SQLite fixtures are used. Neither policy nor
witness is trusted time, consent, a dispatch, or notification permission.
"""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_quarantine_ledger as quarantine


class PoisonField:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("getter")
        raise AssertionError("poisoned input field must not execute")


def _fixture(tmp_path):
    policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine-inputs.sqlite", policy=policy, create=True,
    )
    return ledger, policy, quarantine.genesis_quarantine_witness(policy)


def _review(action, ledger, policy, witness):
    if action == "inspect":
        return ledger.inspect(retained=witness)
    return ledger.quarantine_expired(
        index=0,
        occurrence_id=quarantine.derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=witness,
    )


@pytest.mark.parametrize("action", ("inspect", "quarantine"))
@pytest.mark.parametrize("carrier,field", (
    ("policy", "policy_sha256"),
    ("policy", "first_ms"),
    ("policy", "interval_ms"),
    ("policy", "count"),
    ("policy", "grace_ms"),
    ("witness", "count"),
    ("witness", "chain_sha256"),
))
def test_input_slot_never_invoked_before_local_access(
    tmp_path, monkeypatch, action, carrier, field,
):
    ledger, policy, witness = _fixture(tmp_path)
    calls = []
    opens = []

    def forbidden_connect(*args, **kwargs):
        opens.append(True)
        raise AssertionError("SQLite must not open with forged carrier")

    target = (
        quarantine.QuarantinePolicy
        if carrier == "policy" else quarantine.QuarantineWitness
    )
    with monkeypatch.context() as patch:
        patch.setattr(target, field, PoisonField(calls))
        patch.setattr(quarantine.sqlite3, "connect", forbidden_connect)
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="quarantine input carrier descriptor changed",
        ):
            _review(action, ledger, policy, witness)

    assert calls == []
    assert opens == []
    assert ledger.inspect(retained=witness) == witness


@pytest.mark.parametrize("carrier", ("policy", "witness"))
@pytest.mark.parametrize("hook", ("__init__", "__getattribute__", "__getattr__"))
@pytest.mark.parametrize("action", ("inspect", "quarantine"))
def test_input_hook_refused_without_executing_hook(
    tmp_path, monkeypatch, carrier, hook, action,
):
    ledger, policy, witness = _fixture(tmp_path)
    calls = []

    def poisoned(*args, **kwargs):
        calls.append("hook")
        raise AssertionError("replaced carrier hook must not execute")

    target = (
        quarantine.QuarantinePolicy
        if carrier == "policy" else quarantine.QuarantineWitness
    )
    with monkeypatch.context() as patch:
        patch.setattr(target, hook, poisoned, raising=False)
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="quarantine input carrier descriptor changed",
        ):
            _review(action, ledger, policy, witness)

    assert calls == []
    assert ledger.inspect(retained=witness) == witness


def test_normal_quarantine_witness_is_never_execution_authority(tmp_path):
    ledger, policy, witness = _fixture(tmp_path)
    receipt = _review("quarantine", ledger, policy, witness)
    assert receipt.witness.count == 1
    assert receipt.quarantined_index == 0
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.consent_verified is False
    assert receipt.witness.independently_authenticated is False
