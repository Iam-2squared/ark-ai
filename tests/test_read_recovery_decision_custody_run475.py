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
    monkeypatch.setattr(
        recovery, "ReadRecoveryDecision",
        lambda name, code: SimpleNamespace(
            step_id=name, disposition=code, dispatch_authorized=True,
        ),
    )
    with pytest.raises(recovery.DetachedReadRecoveryRejected, match="decision carrier"):
        _review()


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
    with pytest.raises(recovery.DetachedReadRecoveryRejected, match="decision carrier"):
        _review()


@pytest.mark.parametrize("replacement", ["QUARANTINE_UNCERTAIN", "equal_value_copy"])
def test_decision_changed_during_digest_is_rejected(monkeypatch, replacement):
    old = recovery.ReadRecoveryDecision
    old_hash = recovery.hashlib.sha256
    created = []

    def collect(name, code):
        item = old(name, code)
        created.append(item)
        return item

    def change_then_hash(payload):
        previous = created[0].disposition
        changed = (
            previous.encode("ascii").decode("ascii")
            if replacement == "equal_value_copy" else replacement
        )
        assert changed is not previous
        object.__setattr__(created[0], "disposition", changed)
        return old_hash(payload)

    monkeypatch.setattr(recovery, "ReadRecoveryDecision", collect)
    monkeypatch.setattr(recovery.hashlib, "sha256", change_then_hash)
    with pytest.raises(recovery.DetachedReadRecoveryRejected, match="decision carrier"):
        _review()


def test_result_constructor_cannot_rewrite_nested_decision(monkeypatch):
    original = recovery.DetachedReadRecoverySchedule

    def rewrite(request_id, decisions, digest):
        object.__setattr__(decisions[0], "disposition", "QUARANTINE_UNCERTAIN")
        return original(request_id, decisions, digest)

    monkeypatch.setattr(recovery, "DetachedReadRecoverySchedule", rewrite)
    with pytest.raises(recovery.DetachedReadRecoveryRejected, match="decision carrier"):
        _review()


def test_forged_review_result_is_rejected(monkeypatch):
    monkeypatch.setattr(
        recovery, "DetachedReadRecoverySchedule",
        lambda request_id, decisions, digest: SimpleNamespace(
            request_id=request_id, decisions=decisions,
            schedule_digest=digest, dispatch_authorized=True,
            automatic_replay_authorized=True, external_outcome_verified=True,
        ),
    )
    with pytest.raises(recovery.DetachedReadRecoveryRejected, match="schedule altered"):
        _review()
