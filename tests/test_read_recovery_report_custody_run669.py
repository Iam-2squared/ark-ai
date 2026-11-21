"""Fail-closed detached READ report custody, without backend execution."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_recovery_journal_bridge as bridge
from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _review_empty():
    genesis = genesis_witness()
    steps = (ReadRecoveryStep(_STEP, "math.sum", (), "NOT_STARTED"),)
    return bridge.review_detached_read_journal_recovery(
        _REQUEST, steps, ReadJournalSnapshot(genesis, ()), genesis,
    )


def test_original_report_is_non_authorizing_and_empty_history_is_supported():
    review = _review_empty()
    assert review.successful_step_ids == ()
    assert review.backend_dispatched is False
    assert review.external_result_proven is False
    assert review.automatic_replay_authorized is False
    assert review.independent_custody_proven is False


@pytest.mark.parametrize(
    "member",
    ("__init__", "journal_tip_sha256", "__getattribute__", "external_result_proven"),
)
def test_replaced_report_execution_surface_is_denied_before_any_callback(
    monkeypatch, member,
):
    executed = []

    def malicious(*_args, **_kwargs):
        executed.append(member)
        raise AssertionError("untrusted report callback executed")

    if member == "journal_tip_sha256" or member == "external_result_proven":
        replacement = property(malicious)
    else:
        replacement = malicious
    monkeypatch.setattr(bridge.ReadRecoveryJournalReview, member, replacement)
    with pytest.raises(
        bridge.ReadRecoveryJournalRejected, match="authority definition",
    ):
        _review_empty()
    assert executed == []
