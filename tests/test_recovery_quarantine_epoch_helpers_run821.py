"""Pinned digest helpers and exact identity epochs for inert recovery inventory."""

from __future__ import annotations

import hashlib
import json

import pytest

from ark.agency import disconnected_recovery_quarantine_inventory as inventory
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    AtomicUnknownOutcomeReview,
)
from ark.agency.disconnected_planner_slot_restart_bridge import (
    DisconnectedPlannerSlotBridge,
)
from ark.memory.ambiguous_commit_pair_review import MemoryAmbiguityPair


@pytest.mark.parametrize("helper", ("_sha", "_digest", "_same_leaf_epoch"))
def test_substituted_inventory_helper_refused_before_invocation(
    monkeypatch: pytest.MonkeyPatch, helper: str,
) -> None:
    called = []

    def attacker(*_args, **_kwargs):
        called.append(helper)
        raise AssertionError("rebound helper must not execute")

    monkeypatch.setattr(inventory, helper, attacker)
    with pytest.raises(
        inventory.DisconnectedRecoveryInventoryRejected,
        match="protocol changed",
    ):
        inventory.review_disconnected_recovery_quarantine(object(), object(), ())
    assert called == []


@pytest.mark.parametrize(
    ("current", "pinned"),
    (
        ((False,), (0,)),
        ((1.0,), (1,)),
        ((0,), (False,)),
        ((("x",),), (("x", "x"),)),
    ),
)
def test_equal_numeric_or_changed_nested_epoch_is_not_identical(
    current: tuple[object, ...], pinned: tuple[object, ...],
) -> None:
    assert inventory._same_leaf_epoch(current, pinned) is False


def test_comparison_never_invokes_hostile_equality() -> None:
    called = []

    class Hostile:
        def __eq__(self, _other):
            called.append(True)
            raise AssertionError("untrusted __eq__ reached")

    before, after = Hostile(), Hostile()
    assert inventory._same_leaf_epoch((before,), (before,)) is True
    assert inventory._same_leaf_epoch((after,), (before,)) is False
    assert inventory._same_leaf_epoch((before,), (0,)) is False
    assert called == []


def test_canonical_local_receipts_remain_inert_and_reproducible() -> None:
    def digest(domain: bytes, parts: object) -> str:
        raw = json.dumps(
            parts, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        ).encode("ascii")
        return hashlib.sha256(domain + raw).hexdigest()

    memory_fields = (
        "LOCAL_UNCHANGED_REVIEW", "a" * 64, "b" * 64, "c" * 64,
        "d" * 64, "e" * 64,
    )
    memory = MemoryAmbiguityPair(
        *memory_fields,
        digest(b"ARK-memory-ambiguous-dual-review-v1\0", memory_fields),
    )
    planner_fields = (
        "1" * 64, "2" * 64, "3" * 64, ("step-a",), (), 0,
    )
    planner = DisconnectedPlannerSlotBridge(
        *planner_fields,
        digest(
            b"ARK-disconnected-planner-slot-restart-bridge-v1\0",
            planner_fields,
        ),
    )
    atomic = (AtomicUnknownOutcomeReview("occ_" + "a" * 64,
                                        "UNCHANGED", 0, 0, False),)
    result = inventory.review_disconnected_recovery_quarantine(
        memory, planner, atomic,
    )
    again = inventory.review_disconnected_recovery_quarantine(
        memory, planner, atomic,
    )
    assert result.inventory_sha256 == again.inventory_sha256
    assert result.disposition == "MANUAL_REVIEW_REQUIRED"
    assert result.manual_review_required is True
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trusted_clock_verified is False
