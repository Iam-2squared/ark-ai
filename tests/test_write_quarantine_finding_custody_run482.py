"""Synthetic WRITE quarantine receipts never authorize a real retry or dispatch."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.synthetic_write_quarantine_matrix_review as quarantine

_PLAN = "plan_" + "a" * 64
_IDS = ("write_a", "write_b")
_ROWS = (
    quarantine.SyntheticWriteStoreObservation(
        "write_a", "pending", "absent", "absent", "absent",
    ),
    quarantine.SyntheticWriteStoreObservation(
        "write_b", "running", "present", "present", "present",
    ),
)


def _review(rows=_ROWS):
    return quarantine.diagnose_disconnected_write_quarantine(
        topology_digest=_PLAN,
        independently_expected_step_ids=_IDS,
        observations=rows,
    )


def test_complete_quarantine_matrix_never_grants_write():
    result = _review()
    assert len(result.findings) == 2
    assert result.observed_write_step_ids == _IDS
    assert all(
        finding.automatic_replay_authorized is False
        for finding in result.findings
    )
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "no_external_nonexecution_proof" in result.findings[0].reasons


def test_row_state_changes_local_digest_without_granting_authority():
    original = _review()
    updated = _review((replace(_ROWS[0], plan_state="failed"), _ROWS[1]))
    assert original.local_digest != updated.local_digest
    assert updated.dispatch_authorized is False
    assert updated.findings[0].automatic_replay_authorized is False


def test_reject_replaced_finding_constructor(monkeypatch):
    monkeypatch.setattr(
        quarantine, "SyntheticQuarantineFinding", lambda *args: object(),
    )
    with pytest.raises(
        quarantine.SyntheticQuarantineMatrixRejected, match="finding carrier",
    ):
        _review()


def test_reject_mutation_of_earlier_finding_in_later_constructor(monkeypatch):
    original = quarantine.SyntheticQuarantineFinding
    created = []

    def construct(*args):
        if created:
            object.__setattr__(created[0], "reasons", ("forged",))
        item = original(*args)
        created.append(item)
        return item

    monkeypatch.setattr(quarantine, "SyntheticQuarantineFinding", construct)
    with pytest.raises(
        quarantine.SyntheticQuarantineMatrixRejected, match="carrier changed",
    ):
        _review()


def test_reject_finding_auto_replay_property_forgery(monkeypatch):
    monkeypatch.setattr(
        quarantine.SyntheticQuarantineFinding,
        "automatic_replay_authorized", property(lambda self: True),
    )
    with pytest.raises(
        quarantine.SyntheticQuarantineMatrixRejected, match="finding carrier",
    ):
        _review()


def test_reject_replaced_matrix_constructor(monkeypatch):
    monkeypatch.setattr(
        quarantine, "SyntheticQuarantineMatrix", lambda *args: object(),
    )
    with pytest.raises(
        quarantine.SyntheticQuarantineMatrixRejected, match="result changed",
    ):
        _review()


def test_reject_matrix_returned_with_swapped_findings(monkeypatch):
    original = quarantine.SyntheticQuarantineMatrix

    def altered(*args):
        value = original(*args)
        object.__setattr__(value, "findings", tuple(reversed(args[2])))
        return value

    monkeypatch.setattr(quarantine, "SyntheticQuarantineMatrix", altered)
    with pytest.raises(
        quarantine.SyntheticQuarantineMatrixRejected, match="result changed",
    ):
        _review()


@pytest.mark.parametrize("flag", [
    "dispatch_authorized",
    "automatic_replay_authorized",
    "external_outcome_known",
])
def test_reject_forged_result_authority(monkeypatch, flag):
    monkeypatch.setattr(
        quarantine.SyntheticQuarantineMatrix,
        flag, property(lambda self: True),
    )
    with pytest.raises(
        quarantine.SyntheticQuarantineMatrixRejected, match="result changed",
    ):
        _review()
