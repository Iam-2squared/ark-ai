"""Bounded, disconnected cross-store uncertainty is never retry authority."""

from dataclasses import FrozenInstanceError

import pytest

import ark.agency.synthetic_write_quarantine_matrix_review as matrix

_TOPOLOGY = "plan_" + "e" * 64


def _row(name="a", plan="pending", reservation="absent",
         audit="absent", link="absent"):
    return matrix.SyntheticWriteStoreObservation(
        name, plan, reservation, audit, link,
    )


def _diagnose(rows, names=None):
    return matrix.diagnose_disconnected_write_quarantine(
        topology_digest=_TOPOLOGY,
        independently_expected_step_ids=(
            names if names is not None else tuple(sorted(row.step_id for row in rows))
        ),
        observations=rows,
    )


def test_no_evidence_cannot_authorize_replay():
    result = _diagnose((_row(),))
    assert len(result.findings) == 1
    assert result.findings[0].reasons == ("no_external_nonexecution_proof",)
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_known
    assert not result.findings[0].automatic_replay_authorized
    with pytest.raises(FrozenInstanceError):
        result.local_digest = "changed"


@pytest.mark.parametrize(
    "state", ("pending", "running", "succeeded", "failed", "blocked"),
)
def test_every_planner_state_remains_quarantined(state):
    found = _diagnose((_row(plan=state),)).findings[0]
    assert "no_external_nonexecution_proof" in found.reasons
    if state == "running":
        assert "planner_running_uncertain" in found.reasons
    if state in ("succeeded", "failed", "blocked"):
        assert "planner_terminal_unverified" in found.reasons
    assert not found.automatic_replay_authorized


@pytest.mark.parametrize("field", ("reservation", "preaction_audit", "audit_link"))
def test_each_unavailable_store_preserves_quarantine(field):
    values = {"reservation": "absent", "preaction_audit": "absent", "audit_link": "absent"}
    values[field] = "unavailable"
    found = _diagnose((
        matrix.SyntheticWriteStoreObservation("a", "pending", **values),
    )).findings[0]
    assert "store_unavailable" in found.reasons


def test_orphan_link_is_reported_without_repair_or_retry():
    found = _diagnose((_row(reservation="absent", audit="absent", link="present"),)).findings[0]
    assert "cross_store_orphan" in found.reasons
    assert not found.automatic_replay_authorized


@pytest.mark.parametrize("rows", (
    (_row("a"),),
    (_row("a"), _row("c")),
    (_row("b"), _row("a")),
    (_row("a"), _row("a")),
))
def test_missing_extra_reordered_and_duplicate_recovery_rows_fail(rows):
    with pytest.raises(matrix.SyntheticQuarantineMatrixRejected):
        _diagnose(rows, names=("a", "b"))


@pytest.mark.parametrize("bad", (
    None, True, "", "unknown", 0,
))
def test_noncanonical_evidence_state_fails_closed(bad):
    with pytest.raises(matrix.SyntheticQuarantineMatrixRejected):
        _diagnose((_row(reservation=bad),))


def test_stable_digest_across_identical_synthetic_recovery_rows():
    first = _diagnose((_row("a"), _row("b", "running", "present", "present", "present")))
    again = _diagnose((_row("a"), _row("b", "running", "present", "present", "present")))
    assert first == again
    assert first.local_digest.startswith("quarantine_")
    assert "reservation_already_persisted" in first.findings[1].reasons


def test_reflected_change_during_local_digest_fails_closed(monkeypatch):
    row = _row()
    original = matrix._hash

    def mutate(payload):
        object.__setattr__(row, "plan_state", "running")
        return original(payload)

    monkeypatch.setattr(matrix, "_hash", mutate)
    with pytest.raises(matrix.SyntheticQuarantineMatrixRejected):
        _diagnose((row,))


@pytest.mark.parametrize("names", (
    (), ("a", "a"), ("b", "a"), ("a",) * 129,
    (" ",), ("bad\ud800",), ("a" * 257,),
))
def test_independent_membership_shape_rejects_bad_identifiers(names):
    rows = tuple(_row(name) for name in names)
    with pytest.raises(matrix.SyntheticQuarantineMatrixRejected):
        matrix.diagnose_disconnected_write_quarantine(
            topology_digest=_TOPOLOGY,
            independently_expected_step_ids=names,
            observations=rows,
        )
