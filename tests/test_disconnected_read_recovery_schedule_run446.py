"""Fail-closed detached, in-memory READ recovery decisions."""

from dataclasses import FrozenInstanceError

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    DetachedReadRecoverySchedule,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

REQ = "req_" + "a" * 32
ONE = "step_" + "1" * 16
TWO = "step_" + "2" * 16
THREE = "step_" + "3" * 16
FOUR = "step_" + "4" * 16
SHA = "f" * 64


def node(id=ONE, deps=(), state="NOT_STARTED", digest=None, operation="math.sum"):
    return ReadRecoveryStep(id, operation, deps, state, digest)


def schedule(*rows, request_id=REQ):
    return schedule_detached_read_recovery(request_id, tuple(rows))


def names(result):
    return tuple(row.disposition for row in result.decisions)


def test_all_unstarted_separate_roots_are_mock_hints_only():
    result = schedule(node(), node(TWO))
    assert type(result) is DetachedReadRecoverySchedule
    assert names(result) == ("READY_MOCK_ONLY", "READY_MOCK_ONLY")
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_verified
    assert len(result.schedule_digest) == 64
    with pytest.raises(FrozenInstanceError):
        result.schedule_digest = SHA


def test_pending_chain_and_dependency_wait():
    result = schedule(node(), node(TWO, (ONE,)), node(THREE, (TWO,)))
    assert names(result) == (
        "READY_MOCK_ONLY", "WAIT_DEPENDENCY", "WAIT_DEPENDENCY",
    )


def test_completed_dependency_allows_mock_hint_only():
    result = schedule(node(state="SUCCEEDED", digest=SHA), node(TWO, (ONE,)))
    assert names(result) == ("COMPLETE_UNVERIFIED", "READY_MOCK_ONLY")


@pytest.mark.parametrize("state", ["RUNNING", "UNKNOWN"])
def test_ambiguous_state_quarantines_all_descendants(state):
    result = schedule(
        node(state=state), node(TWO, (ONE,)), node(THREE, (TWO,)), node(FOUR),
    )
    assert names(result) == (
        "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN", "HOLD_UNCERTAIN",
        "READY_MOCK_ONLY",
    )


def test_failed_state_terminally_holds_descendants():
    result = schedule(node(state="FAILED"), node(TWO, (ONE,)), node(THREE, (TWO,)))
    assert names(result) == ("TERMINAL_FAILURE", "HOLD_FAILED", "HOLD_FAILED")


def test_failed_dependency_takes_precedence_over_pending():
    result = schedule(node(state="FAILED"), node(TWO), node(THREE, (ONE, TWO)))
    assert names(result) == (
        "TERMINAL_FAILURE", "READY_MOCK_ONLY", "HOLD_FAILED",
    )


def test_deterministic_digest_contains_untrusted_state_changes():
    base = schedule(node(), node(TWO, (ONE,)))
    assert base == schedule(node(), node(TWO, (ONE,)))
    changed = schedule(node(state="FAILED"), node(TWO, (ONE,)))
    assert base.schedule_digest != changed.schedule_digest
    assert base.schedule_digest != schedule(node()).schedule_digest


@pytest.mark.parametrize("value", [None, True, "", "req_" + "A" * 32, "req_b"])
def test_bad_request_identity_fails_closed(value):
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule(node(), request_id=value)


@pytest.mark.parametrize("rows", [
    (), (node(), node()),
    (node(ONE, (TWO,)), node(TWO)),
    (node(ONE, (ONE,)),),
    (node(ONE, ()), node(TWO, (ONE, ONE))),
    (node(ONE), node(TWO, (THREE,))),
    (node(ONE), node(TWO, (ONE, "x"))),
    (node(ONE, state="SUCCEEDED"),),
    (node(ONE, state="FAILED", digest=SHA),),
    (node(ONE, state="UNKNOWN", digest=SHA),),
    (node(ONE, state="SUCCEEDED", digest="BAD"),),
    (node(ONE, state="RUNNING"), node(TWO, (ONE,), "SUCCEEDED", SHA)),
    (node(ONE, state="FAILED"), node(TWO, (ONE,), "SUCCEEDED", SHA)),
    (node(ONE, state="NOT_STARTED"), node(TWO, (ONE,), "SUCCEEDED", SHA)),
    (node(ONE, operation="shell.exec"),),
    (node(ONE, state="bad"),),
    (node(ONE, deps=[]),),
    (node("step_" + "X" * 16),),
])
def test_bad_graph_or_history_fails_closed(rows):
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule(*rows)


def test_exact_type_and_length_budgets():
    class Child(ReadRecoveryStep):
        pass
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule(Child(ONE, "math.sum", (), "NOT_STARTED"))
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule_detached_read_recovery(REQ, [node()])
    large = tuple(node("step_" + f"{n:016x}") for n in range(25))
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule(*large)


def test_max_24_and_never_auto_replay_even_all_completed():
    rows = tuple(node("step_" + f"{n:016x}", state="SUCCEEDED", digest=SHA)
                 for n in range(24))
    result = schedule(*rows)
    assert len(result.decisions) == 24
    assert all(row.disposition == "COMPLETE_UNVERIFIED" for row in result.decisions)
    assert not result.automatic_replay_authorized


def test_reflective_mutation_during_hash_is_rejected(monkeypatch):
    from ark.agency import disconnected_read_recovery_schedule as mod
    item = node()
    original = mod.hashlib.sha256
    def switched(data):
        object.__setattr__(item, "operation", item.operation.encode().decode())
        return original(data)
    monkeypatch.setattr(mod.hashlib, "sha256", switched)
    with pytest.raises(DetachedReadRecoveryRejected, match="carrier changed"):
        schedule(item)


def test_relabelled_digest_rejected_even_if_equal_value(monkeypatch):
    from ark.agency import disconnected_read_recovery_schedule as mod
    completed = node(state="SUCCEEDED", digest=SHA)
    original = mod.hashlib.sha256
    def switched(data):
        object.__setattr__(completed, "result_sha256", SHA.encode().decode())
        return original(data)
    monkeypatch.setattr(mod.hashlib, "sha256", switched)
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule(completed)
