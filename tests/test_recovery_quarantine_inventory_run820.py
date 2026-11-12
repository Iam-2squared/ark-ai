"""Digest-only cross-domain quarantine; no implicit startup/action authority."""

from __future__ import annotations

import hashlib
import json

import pytest

from ark.agency.disconnected_atomic_unknown_outcome_review import (
    AtomicUnknownOutcomeReview,
)
from ark.agency.disconnected_planner_slot_restart_bridge import (
    DisconnectedPlannerSlotBridge,
)
import ark.agency.disconnected_recovery_quarantine_inventory as inventory
from ark.memory.ambiguous_commit_pair_review import MemoryAmbiguityPair


def _digest(domain: bytes, values: object) -> str:
    body = json.dumps(
        values, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(domain + body).hexdigest()


def _memory(
    disposition: str = "LOCAL_UNCHANGED_REVIEW",
) -> MemoryAmbiguityPair:
    fields = (
        disposition, "a" * 64, "b" * 64, "c" * 64, "d" * 64, "e" * 64,
    )
    return MemoryAmbiguityPair(
        *fields, _digest(b"ARK-memory-ambiguous-dual-review-v1\0", fields),
    )


def _planner(
    unknown: tuple[str, ...] = (),
) -> DisconnectedPlannerSlotBridge:
    fields = (
        "1" * 64, "2" * 64, "3" * 64,
        ("step-a", "step-b"), unknown, 0,
    )
    return DisconnectedPlannerSlotBridge(
        *fields, _digest(
            b"ARK-disconnected-planner-slot-restart-bridge-v1\0", fields,
        ),
    )


def _atomic(
    occurrence: str = "a", state: str = "UNCHANGED",
) -> AtomicUnknownOutcomeReview:
    before, observed, present = {
        "UNCHANGED": (0, 0, False),
        "LOCALLY_RECORDED": (0, 1, True),
        "PREEXISTING": (1, 1, True),
        "ADVANCED_OTHER": (0, 1, False),
    }[state]
    return AtomicUnknownOutcomeReview(
        "occ_" + occurrence * 64, state, before, observed, present,
    )


def _review(
    memory: MemoryAmbiguityPair | None = None,
    planner: DisconnectedPlannerSlotBridge | None = None,
    atoms: tuple[AtomicUnknownOutcomeReview, ...] | None = None,
) -> inventory.DisconnectedRecoveryQuarantineInventory:
    return inventory.review_disconnected_recovery_quarantine(
        _memory() if memory is None else memory,
        _planner() if planner is None else planner,
        (_atomic(),) if atoms is None else atoms,
    )


def _no_authority(result: inventory.DisconnectedRecoveryQuarantineInventory) -> None:
    assert result.manual_review_required is True
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_authenticated is False
    assert result.cross_store_atomicity_proven is False
    assert result.external_effect_verified is False
    assert result.trusted_clock_verified is False


def test_unchanged_inputs_still_require_manual_review() -> None:
    result = _review()
    assert result.disposition == "MANUAL_REVIEW_REQUIRED"
    assert result.held_step_count == 2
    assert result.unknown_step_count == 0
    assert result.observed_occurrence_count == 1
    assert result.locally_present_count == 0
    _no_authority(result)


@pytest.mark.parametrize("state", (
    "LOCALLY_RECORDED", "PREEXISTING", "ADVANCED_OTHER",
))
def test_local_atomic_states_never_allow_replay(state: str) -> None:
    result = _review(atoms=(_atomic(state=state),))
    assert result.disposition == "QUARANTINED"
    assert result.locally_present_count == int(state != "ADVANCED_OTHER")
    _no_authority(result)


@pytest.mark.parametrize("disposition", (
    "MATCHING_ROW_MANUAL_REVIEW", "DIVERGED_MANUAL_REVIEW",
))
def test_memory_change_preserves_quarantine(disposition: str) -> None:
    result = _review(memory=_memory(disposition))
    assert result.disposition == "QUARANTINED"
    _no_authority(result)


def test_planner_unknown_maintains_manual_quarantine() -> None:
    result = _review(planner=_planner(("step-b",)))
    assert result.unknown_step_count == 1
    assert result.disposition == "QUARANTINED"
    _no_authority(result)


def test_multi_occurrence_counts_no_external_effect_claim() -> None:
    result = _review(atoms=(_atomic("a"), _atomic("b", "LOCALLY_RECORDED")))
    assert result.observed_occurrence_count == 2
    assert result.locally_present_count == 1
    _no_authority(result)


def test_forged_memory_child_digest_is_refused() -> None:
    m = _memory()
    object.__setattr__(m, "reconciliation_sha256", "f" * 64)
    with pytest.raises(inventory.DisconnectedRecoveryInventoryRejected):
        _review(memory=m)


def test_forged_planner_child_digest_is_refused() -> None:
    p = _planner()
    object.__setattr__(p, "bridge_sha256", "f" * 64)
    with pytest.raises(inventory.DisconnectedRecoveryInventoryRejected):
        _review(planner=p)


@pytest.mark.parametrize("report", (
    AtomicUnknownOutcomeReview("occ_" + "a" * 64, "UNCHANGED", 0, 1, False),
    AtomicUnknownOutcomeReview("occ_" + "a" * 64, "PREEXISTING", 0, 0, True),
    AtomicUnknownOutcomeReview("occ_" + "a" * 64, "ADVANCED_OTHER", 0, 1, True),
    AtomicUnknownOutcomeReview("occ_" + "a" * 64, "LOCALLY_RECORDED", 1, 1, True),
    AtomicUnknownOutcomeReview("occ_" + "a" * 64, "UNCHANGED", True, 0, False),
))
def test_inconsistent_atomic_receipts_refuse(report: AtomicUnknownOutcomeReview) -> None:
    with pytest.raises(inventory.DisconnectedRecoveryInventoryRejected):
        _review(atoms=(report,))


@pytest.mark.parametrize("atoms", (
    (),
    (_atomic("a"), _atomic("a")),
    (_atomic("b"), _atomic("a")),
    tuple(_atomic("a") for _ in range(17)),
))
def test_missing_duplicate_unordered_or_unbounded_occurrences_refuse(
    atoms: tuple[AtomicUnknownOutcomeReview, ...],
) -> None:
    with pytest.raises(inventory.DisconnectedRecoveryInventoryRejected):
        _review(atoms=atoms)


def test_late_authority_descriptor_replacement_refused_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched = []

    def attacker(_self):
        touched.append(True)
        return True

    monkeypatch.setattr(
        AtomicUnknownOutcomeReview, "dispatch_authorized", property(attacker),
    )
    with pytest.raises(
        inventory.DisconnectedRecoveryInventoryRejected,
        match="protocol changed",
    ):
        _review()
    assert touched == []


def test_caller_supplied_receipt_is_not_trusted_identity() -> None:
    result = _review()
    assert result.disposition == "MANUAL_REVIEW_REQUIRED"
    assert result.plan_id == "1" * 64
    assert len(result.inventory_sha256) == 64
    assert all(x not in repr(result) for x in ("private text", "permission granted"))
    _no_authority(result)
