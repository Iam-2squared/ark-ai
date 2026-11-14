"""Offline Planner terminal/occurrence states never release synthetic WRITE.

A matching local record, even with all stores reporting absent, is neither an
external nonexecution proof nor an automatic-replay entitlement.
"""

from __future__ import annotations

import pytest

from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticQuarantineMatrixRejected,
    SyntheticWriteStoreObservation,
    diagnose_disconnected_write_quarantine,
)

_TOPOLOGY = "plan_" + "a" * 64
_IDS = ("step-a",)


def _diagnose(
    state: str,
    reservation: str = "absent",
    preaction: str = "absent",
    audit_link: str = "absent",
):
    return diagnose_disconnected_write_quarantine(
        topology_digest=_TOPOLOGY,
        independently_expected_step_ids=_IDS,
        observations=(
            SyntheticWriteStoreObservation(
                "step-a", state, reservation, preaction, audit_link,
            ),
        ),
    )


@pytest.mark.parametrize(
    "state", ("pending", "running", "succeeded", "failed", "blocked"),
)
@pytest.mark.parametrize("reservation", ("absent", "present", "unavailable"))
def test_every_planner_terminal_and_occurrence_class_stays_quarantined(
    state: str, reservation: str,
) -> None:
    result = _diagnose(state, reservation)
    finding = result.findings[0]
    assert finding.step_id == "step-a"
    assert "no_external_nonexecution_proof" in finding.reasons
    assert result.observed_write_step_ids == _IDS
    assert result.local_digest.startswith("quarantine_")
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert finding.automatic_replay_authorized is False
    if state == "running":
        assert "planner_running_uncertain" in finding.reasons
    elif state != "pending":
        assert "planner_terminal_unverified" in finding.reasons
    if reservation == "present":
        assert "reservation_already_persisted" in finding.reasons
    elif reservation == "unavailable":
        assert "store_unavailable" in finding.reasons


@pytest.mark.parametrize(
    ("reservation", "preaction", "link"),
    (
        ("absent", "absent", "present"),
        ("present", "absent", "present"),
        ("absent", "present", "present"),
    ),
)
def test_cross_store_orphans_remain_unreplayable(
    reservation: str, preaction: str, link: str,
) -> None:
    result = _diagnose("pending", reservation, preaction, link)
    reasons = result.findings[0].reasons
    assert "cross_store_orphan" in reasons
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("invalid", ("cancelled", "unknown", "SUCCEEDED"))
def test_unrecognized_plan_state_is_never_coerced_to_pending(invalid: str) -> None:
    with pytest.raises(SyntheticQuarantineMatrixRejected):
        _diagnose(invalid)


def test_same_input_generates_stable_non_authorizing_local_digest() -> None:
    left = _diagnose("failed", "present", "present", "present")
    right = _diagnose("failed", "present", "present", "present")
    assert left.local_digest == right.local_digest
    assert left.external_outcome_known is False
    assert right.dispatch_authorized is False
