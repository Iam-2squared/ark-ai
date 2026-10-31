"""No ambiguous mixed-plan WRITE can become an authorized restart action."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFence,
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

PLAN = "plan_" + "a" * 64
A = "step_" + "1" * 16
B = "step_" + "2" * 16
C = "step_" + "3" * 16
SLOT = "slot_" + "b" * 64
DIGEST = "c" * 64


def item(name, effect="READ", deps=(), state="PENDING", result=None, reservation=None):
    return OfflineRecoveryStepClaim(name, effect, deps, state, result, reservation)


def result(*steps):
    return review_disconnected_recovery_fence(PLAN, steps)


def codes(view):
    return tuple(value.code for value in view.decisions)


def test_independent_read_ready_write_never_ready():
    review = result(item(A), item(B, "WRITE"))
    assert codes(review) == ("READY_MOCK_ONLY", "HELD_WRITE_APPROVAL")
    assert not review.dispatch_authorized
    assert not review.automatic_replay_authorized
    assert not review.write_authorized
    assert not review.external_outcome_verified
    with pytest.raises(FrozenInstanceError):
        review.digest = "0" * 64


def test_reserved_pending_write_quarantines_read_descendants():
    review = result(item(A, "WRITE", reservation=SLOT), item(B, deps=(A,)))
    assert codes(review) == ("QUARANTINE_RESERVED_WRITE", "HOLD_UNCERTAIN")


@pytest.mark.parametrize("state", ["RUNNING", "UNKNOWN"])
def test_uncertain_write_not_replayed(state):
    review = result(item(A, "WRITE", state=state), item(B, deps=(A,)))
    assert codes(review) == ("QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN")
    assert not review.automatic_replay_authorized


@pytest.mark.parametrize("state", ["FAILED", "CANCELLED", "BLOCKED"])
def test_terminal_descendant_holds(state):
    review = result(item(A, state=state), item(B, deps=(A,)))
    assert codes(review) == ("TERMINAL", "HOLD_TERMINAL")


def test_succeeded_unverified_and_successors():
    review = result(
        item(A, state="SUCCEEDED", result=DIGEST),
        item(B, "WRITE", (A,), "PENDING"),
        item(C, deps=(A,)),
    )
    assert codes(review) == (
        "COMPLETE_UNVERIFIED", "HELD_WRITE_APPROVAL", "READY_MOCK_ONLY",
    )


def test_uncertain_isolation_keeps_unrelated_read_mockable():
    review = result(
        item(A, "WRITE", state="UNKNOWN"), item(B, deps=(A,)), item(C),
    )
    assert codes(review) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN", "READY_MOCK_ONLY",
    )


def test_bad_success_or_running_predecessor_rejected():
    for state, digest in [("SUCCEEDED", DIGEST), ("RUNNING", None)]:
        with pytest.raises(OfflineRecoveryFenceRejected, match="prerequisites"):
            result(item(A), item(B, deps=(A,), state=state, result=digest))


@pytest.mark.parametrize("claim", [
    item(A, effect="write"), item(A, effect=True), item(A, state="DONE"),
    item(A, result=DIGEST), item(A, state="SUCCEEDED"),
    item(A, state="SUCCEEDED", result="A" * 64),
    item(A, effect="READ", reservation=SLOT),
    item(A, effect="WRITE", reservation="slot_wrong"),
    item(A, effect="WRITE", reservation=True),
    item(A, deps=(B,)), item(A, deps=[B]),
    item(A, state=True),
])
def test_malformed_claim_rejected(claim):
    with pytest.raises(OfflineRecoveryFenceRejected):
        result(claim)


def test_duplicate_dependency_and_forward_edge_rejected():
    with pytest.raises(OfflineRecoveryFenceRejected):
        result(item(A), item(B, deps=(A, A)))
    with pytest.raises(OfflineRecoveryFenceRejected):
        result(item(B, deps=(A,)), item(A))


def test_duplicate_step_and_unordered_dependency_rejected():
    with pytest.raises(OfflineRecoveryFenceRejected):
        result(item(A), item(A))
    with pytest.raises(OfflineRecoveryFenceRejected):
        result(item(A), item(B), item(C, deps=(B, A)))


def test_more_than_24_steps_rejected():
    steps = tuple(item("step_" + f"{x:016x}") for x in range(25))
    with pytest.raises(OfflineRecoveryFenceRejected):
        review_disconnected_recovery_fence(PLAN, steps)


@pytest.mark.parametrize("bad", [None, True, 1, "a" * 64, "plan_" + "A" * 64])
def test_bad_plan_id_rejected(bad):
    with pytest.raises(OfflineRecoveryFenceRejected):
        review_disconnected_recovery_fence(bad, (item(A),))


def test_types_and_immutable_claim_carrier():
    assert len(result(item(A)).digest) == 64
    with pytest.raises(OfflineRecoveryFenceRejected):
        review_disconnected_recovery_fence(PLAN, [item(A)])
    with pytest.raises(OfflineRecoveryFenceRejected):
        review_disconnected_recovery_fence(PLAN, ())
    with pytest.raises(FrozenInstanceError):
        item(A).state = "SUCCEEDED"


def test_nested_terminal_precedence_and_no_write_ready():
    review = result(
        item(A, "WRITE", reservation=SLOT),
        item(B, state="CANCELLED"),
        item(C, deps=(A, B)),
    )
    assert codes(review) == (
        "QUARANTINE_RESERVED_WRITE", "TERMINAL", "HOLD_TERMINAL",
    )


def test_result_authority_getter_cannot_rewrite_original_step(monkeypatch):
    claim = item(A)

    def forged(self):
        object.__setattr__(claim, "state", "UNKNOWN")
        return False

    monkeypatch.setattr(
        OfflineRecoveryFence, "external_outcome_verified", property(forged),
    )
    with pytest.raises(OfflineRecoveryFenceRejected, match="carrier mutated"):
        result(claim)


def test_result_authority_getter_cannot_rewrite_disposition(monkeypatch):
    def forged(self):
        object.__setattr__(self.decisions[0], "code", "HELD_WRITE_APPROVAL")
        return False

    monkeypatch.setattr(
        OfflineRecoveryFence, "external_outcome_verified", property(forged),
    )
    with pytest.raises(OfflineRecoveryFenceRejected, match="disposition changed"):
        result(item(A))


def test_result_authority_getter_cannot_rewrite_digest(monkeypatch):
    def forged(self):
        object.__setattr__(self, "digest", "0" * 64)
        return False

    monkeypatch.setattr(
        OfflineRecoveryFence, "external_outcome_verified", property(forged),
    )
    with pytest.raises(OfflineRecoveryFenceRejected, match="result carrier changed"):
        result(item(A))
