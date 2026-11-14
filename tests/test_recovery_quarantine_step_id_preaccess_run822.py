"""Fail-closed recovered Planner IDs before a local quarantine hash/sort.

Synthetic receipts only; these tests do not open databases or dispatch tools.
"""

from __future__ import annotations

import hashlib
import json

import pytest

import ark.agency.disconnected_recovery_quarantine_inventory as review
from ark.agency.disconnected_atomic_unknown_outcome_review import AtomicUnknownOutcomeReview
from ark.agency.disconnected_planner_slot_restart_bridge import DisconnectedPlannerSlotBridge
from ark.memory.ambiguous_commit_pair_review import MemoryAmbiguityPair


def _digest(domain: bytes, payload: object) -> str:
    return hashlib.sha256(
        domain + json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def _memory() -> MemoryAmbiguityPair:
    fields = ("LOCAL_UNCHANGED_REVIEW",) + tuple(c * 64 for c in "abcde")
    return MemoryAmbiguityPair(
        *fields, _digest(b"ARK-memory-ambiguous-dual-review-v1\0", fields),
    )


def _planner(held: tuple[str, ...], unknown: tuple[str, ...]) -> DisconnectedPlannerSlotBridge:
    fields = ("1" * 64, "2" * 64, "3" * 64, held, unknown, 0)
    return DisconnectedPlannerSlotBridge(
        *fields, _digest(
            b"ARK-disconnected-planner-slot-restart-bridge-v1\0", fields,
        ),
    )


def _review(plan: DisconnectedPlannerSlotBridge) -> review.DisconnectedRecoveryQuarantineInventory:
    return review.review_disconnected_recovery_quarantine(
        _memory(), plan,
        (AtomicUnknownOutcomeReview("occ_" + "a" * 64, "UNCHANGED", 0, 0, False),),
    )


@pytest.mark.parametrize("field", ("held_step_ids", "unknown_step_ids"))
@pytest.mark.parametrize("method", ("hash", "lt"))
def test_hostile_untrusted_step_objects_refused_without_evaluation(
    field: str, method: str,
) -> None:
    touched: list[str] = []

    class Hostile:
        def __hash__(self) -> int:
            touched.append("hash")
            raise AssertionError("hostile hash executed")

        def __lt__(self, other: object) -> bool:
            touched.append("lt")
            raise AssertionError("hostile sort executed")

        def __eq__(self, other: object) -> bool:
            touched.append("eq")
            raise AssertionError("hostile comparison executed")

    plan = _planner(("step-a", "step-b"), ())
    # A frozen receipt can be changed reflectively after construction.
    object.__setattr__(plan, field, (Hostile(),))
    with pytest.raises(review.DisconnectedRecoveryInventoryRejected):
        _review(plan)
    assert touched == []


@pytest.mark.parametrize("bad_id", (
    "", "x" * 257, "界" * 86, "step\x00name", "bad\ud800",
))
@pytest.mark.parametrize("field", ("held_step_ids", "unknown_step_ids"))
def test_unbounded_or_non_utf8_ids_rejected_before_digest(
    bad_id: str, field: str,
) -> None:
    plan = _planner(("step-a", "step-b"), ())
    object.__setattr__(plan, field, (bad_id,))
    with pytest.raises(review.DisconnectedRecoveryInventoryRejected):
        _review(plan)


def test_bounded_256_byte_id_is_admitted_without_authority() -> None:
    long_id = "a" * 256
    plan = _planner((long_id, "step-b"), (long_id,))
    result = _review(plan)
    assert result.disposition == "QUARANTINED"
    assert result.unknown_step_count == 1
    assert result.manual_review_required is True
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_long_untrusted_unknown_inventory_refused_before_sort() -> None:
    plan = _planner(("step-a", "step-b"), ())
    object.__setattr__(plan, "unknown_step_ids", ("step-a",) * 25)
    with pytest.raises(review.DisconnectedRecoveryInventoryRejected):
        _review(plan)


def test_local_step_id_bound_cannot_be_replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(review, "_MAX_STEP_ID_BYTES", 1)
    with pytest.raises(
        review.DisconnectedRecoveryInventoryRejected, match="protocol changed",
    ):
        _review(_planner(("step-a", "step-b"), ()))
