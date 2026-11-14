"""Recovered READ classifications cannot be forged into execution authority."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.agency.disconnected_read_recovery_schedule as recovery

REQ = "req_" + "a" * 32
A = "step_" + "1" * 16
B = "step_" + "2" * 16


def _inputs():
    return (
        recovery.ReadRecoveryStep(A, "math.sum", (), "NOT_STARTED"),
        recovery.ReadRecoveryStep(B, "math.sum", (A,), "NOT_STARTED"),
    )


def _review():
    return recovery.schedule_detached_read_recovery(REQ, _inputs())


def test_unmodified_recovery_remains_inert_and_deterministic():
    one = _review()
    assert one == _review()
    assert tuple(item.disposition for item in one.decisions) == (
        "READY_MOCK_ONLY", "WAIT_DEPENDENCY",
    )
    assert one.dispatch_authorized is False
    assert one.automatic_replay_authorized is False
    assert one.external_outcome_verified is False


def test_forged_first_decision_is_rejected(monkeypatch):
    invoked = []

    def forged(name, code):
        invoked.append((name, code))
        return SimpleNamespace(
            step_id=name, disposition=code, dispatch_authorized=True,
        )

    monkeypatch.setattr(recovery, "ReadRecoveryDecision", forged)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected, match="authority descriptor changed",
    ):
        _review()
    assert invoked == []


def test_earlier_decision_modified_by_later_constructor_is_rejected(monkeypatch):
    old = recovery.ReadRecoveryDecision
    created = []

    def forged(name, code):
        if created:
            object.__setattr__(created[0], "disposition", "QUARANTINE_UNCERTAIN")
        item = old(name, code)
        created.append(item)
        return item

    monkeypatch.setattr(recovery, "ReadRecoveryDecision", forged)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected, match="authority descriptor changed",
    ):
        _review()
    assert created == []


@pytest.mark.parametrize("replacement", ["QUARANTINE_UNCERTAIN", "equal_value_copy"])
def test_decision_changed_during_digest_is_rejected(monkeypatch, replacement):
    # Import-pinned field/lookup custody now refuses the injected hook before
    # any decision is read or the substituted digest callback is invoked.
    original_getattribute = recovery.ReadRecoveryDecision.__getattribute__
    old_hash = recovery.hashlib.sha256
    created = []

    def remember(self, name):
        if name == "step_id" and all(row is not self for row in created):
            created.append(self)
        return original_getattribute(self, name)

    def change_then_hash(payload):
        assert len(created) == 2
        previous = created[0].disposition
        changed = (
            ("!" + previous)[1:]
            if replacement == "equal_value_copy" else replacement
        )
        assert changed is not previous
        object.__setattr__(created[0], "disposition", changed)
        return old_hash(payload)

    monkeypatch.setattr(
        recovery.ReadRecoveryDecision, "__getattribute__", remember,
    )
    monkeypatch.setattr(recovery.hashlib, "sha256", change_then_hash)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="authority descriptor changed",
    ):
        _review()
    assert created == []


def test_result_constructor_cannot_rewrite_nested_decision(monkeypatch):
    # Retain original class identity. A late authorization getter callback
    # can still mutate a previously constructed nested decision.
    original_getattribute = recovery.DetachedReadRecoverySchedule.__getattribute__
    callbacks = []

    def rewrite(self, name):
        callbacks.append(name)
        if name == "dispatch_authorized":
            decisions = original_getattribute(self, "decisions")
            object.__setattr__(decisions[0], "disposition", "QUARANTINE_UNCERTAIN")
            return False
        return original_getattribute(self, name)

    monkeypatch.setattr(
        recovery.DetachedReadRecoverySchedule, "__getattribute__", rewrite,
    )
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="authority descriptor changed",
    ):
        _review()
    assert callbacks == []


def test_forged_review_result_is_rejected(monkeypatch):
    monkeypatch.setattr(
        recovery, "DetachedReadRecoverySchedule",
        lambda request_id, decisions, digest: SimpleNamespace(
            request_id=request_id, decisions=decisions,
            schedule_digest=digest, dispatch_authorized=True,
            automatic_replay_authorized=True, external_outcome_verified=True,
        ),
    )
    with pytest.raises(recovery.DetachedReadRecoveryRejected, match="descriptor changed"):
        _review()
