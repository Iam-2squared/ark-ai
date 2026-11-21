"""READ recovery journal evidence must not promote unrelated DAG branches.

All receipts are disconnected synthetic hashes. Valid chain topology never
establishes a real READ outcome, authority, or safe automatic replay.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_journal_bridge import (
    ReadRecoveryJournalRejected,
    review_detached_read_journal_recovery,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

_REQUEST = "req_" + "a" * 32
_A = "step_" + "1" * 16
_B = "step_" + "2" * 16
_C = "step_" + "3" * 16
_D = "step_" + "4" * 16
_RESULT_A = "a" * 64
_RESULT_C = "c" * 64
_INPUT = "f" * 64


def _evidence(rows):
    prior = genesis_witness().tip_sha256
    for index, row in enumerate(rows, 1):
        prior = _chain(prior, index, row)
    witness = ReadJournalWitness(len(rows), prior)
    return ReadJournalSnapshot(witness, rows), witness


def _steps(root, *, joined="NOT_STARTED"):
    return (
        ReadRecoveryStep(
            _A, "math.sum", (),
            root, _RESULT_A if root == "SUCCEEDED" else None,
        ),
        ReadRecoveryStep(_B, "text.stats", (_A,), "NOT_STARTED"),
        ReadRecoveryStep(_C, "text.find", (), "SUCCEEDED", _RESULT_C),
        ReadRecoveryStep(_D, "json.inspect", (_B, _C), joined),
    )


@pytest.mark.parametrize(
    "root", ("FAILED", "RUNNING", "UNKNOWN", "NOT_STARTED", "SUCCEEDED"),
)
def test_unrelated_success_remains_only_success_for_unresolved_branch(root):
    rows = (
        (ReadReceipt(_REQUEST, _A, "math.sum", _INPUT, _RESULT_A),)
        if root == "SUCCEEDED" else ()
    ) + (ReadReceipt(_REQUEST, _C, "text.find", _INPUT, _RESULT_C),)
    snapshot, retained = _evidence(rows)
    report = review_detached_read_journal_recovery(
        _REQUEST, _steps(root), snapshot, retained,
    )
    expected = (_A, _C) if root == "SUCCEEDED" else (_C,)
    assert report.successful_step_ids == expected
    assert report.journal_tip_sha256 == retained.tip_sha256
    assert report.backend_dispatched is False
    assert report.external_result_proven is False
    assert report.automatic_replay_authorized is False
    assert report.independent_custody_proven is False


@pytest.mark.parametrize("root", ("FAILED", "RUNNING", "UNKNOWN", "NOT_STARTED"))
def test_pending_child_receipt_cannot_be_laundered_by_sibling_success(root):
    rows = (
        ReadReceipt(_REQUEST, _C, "text.find", _INPUT, _RESULT_C),
        ReadReceipt(_REQUEST, _B, "text.stats", _INPUT, "b" * 64),
    )
    snapshot, retained = _evidence(rows)
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            _REQUEST, _steps(root), snapshot, retained,
        )


def test_changed_independent_sibling_result_cannot_be_misbound():
    rows = (ReadReceipt(_REQUEST, _C, "text.find", _INPUT, _RESULT_C),)
    snapshot, retained = _evidence(rows)
    altered = (
        ReadRecoveryStep(_A, "math.sum", (), "UNKNOWN"),
        ReadRecoveryStep(_B, "text.stats", (_A,), "NOT_STARTED"),
        ReadRecoveryStep(_C, "text.find", (), "SUCCEEDED", "e" * 64),
        ReadRecoveryStep(_D, "json.inspect", (_B, _C), "NOT_STARTED"),
    )
    with pytest.raises(ReadRecoveryJournalRejected, match="successful READ"):
        review_detached_read_journal_recovery(
            _REQUEST, altered, snapshot, retained,
        )


def test_receipt_reorder_for_independent_success_changes_tip():
    rows = (
        ReadReceipt(_REQUEST, _A, "math.sum", _INPUT, _RESULT_A),
        ReadReceipt(_REQUEST, _C, "text.find", _INPUT, _RESULT_C),
    )
    left, retained = _evidence(rows)
    right, another = _evidence(tuple(reversed(rows)))
    history = _steps("SUCCEEDED")
    first = review_detached_read_journal_recovery(
        _REQUEST, history, left, retained,
    )
    second = review_detached_read_journal_recovery(
        _REQUEST, history, right, another,
    )
    assert first.successful_step_ids == second.successful_step_ids
    assert first.journal_tip_sha256 != second.journal_tip_sha256
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            _REQUEST, history, replace(right, witness=retained), retained,
        )
