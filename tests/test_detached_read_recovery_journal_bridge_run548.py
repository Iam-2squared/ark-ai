"""Exact SQLite READ receipt / mock DAG recovery linkage, never execution."""

from dataclasses import replace

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
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

REQUEST = "req_" + "a" * 32
OTHER = "req_" + "b" * 32
A = "step_" + "1" * 16
B = "step_" + "2" * 16
C = "step_" + "3" * 16
D1 = "a" * 64
D2 = "b" * 64
INPUT = "c" * 64


def _steps():
    return (
        ReadRecoveryStep(A, "math.sum", (), "SUCCEEDED", D1),
        ReadRecoveryStep(B, "text.stats", (A,), "SUCCEEDED", D2),
        ReadRecoveryStep(C, "text.find", (B,), "NOT_STARTED"),
    )


def _rows():
    return (
        ReadReceipt(REQUEST, A, "math.sum", INPUT, D1),
        ReadReceipt(REQUEST, B, "text.stats", INPUT, D2),
    )


def _snapshot(rows=None):
    if rows is None:
        rows = _rows()
    tip = genesis_witness().tip_sha256
    for index, row in enumerate(rows, 1):
        tip = _chain(tip, index, row)
    witness = ReadJournalWitness(len(rows), tip)
    return ReadJournalSnapshot(witness, rows), witness


def test_sqlite_restart_journal_join_is_inert(tmp_path):
    path = tmp_path / "detached-read.sqlite"
    with DisconnectedReadJournal.create(path) as ledger:
        retained = genesis_witness()
        for row in _rows():
            retained = ledger.append(row, retained)
    with DisconnectedReadJournal.open(path) as reopened:
        snapshot = reopened.recover_receipts(retained)
        review = review_detached_read_journal_recovery(
            REQUEST, _steps(), snapshot, retained,
        )
    assert review.successful_step_ids == (A, B)
    assert review.journal_tip_sha256 == retained.tip_sha256
    assert review.backend_dispatched is False
    assert review.external_result_proven is False
    assert review.automatic_replay_authorized is False
    assert review.independent_custody_proven is False


def test_pending_history_accepts_empty_genesis_only():
    genesis = genesis_witness()
    snapshot = ReadJournalSnapshot(genesis, ())
    steps = (ReadRecoveryStep(A, "math.sum", (), "NOT_STARTED"),)
    review = review_detached_read_journal_recovery(
        REQUEST, steps, snapshot, genesis,
    )
    assert review.successful_step_ids == ()


@pytest.mark.parametrize(
    "steps,rows",
    [
        (_steps(), (_rows()[0],)),
        (_steps(), (_rows()[1], _rows()[0])),
        (_steps(), (_rows()[0], replace(_rows()[1], result_digest=D1))),
        (_steps(), (replace(_rows()[0], request_id=OTHER), _rows()[1])),
        (_steps(), (_rows()[0], _rows()[0])),
        (
            (ReadRecoveryStep(A, "math.sum", (), "NOT_STARTED"),),
            (_rows()[0],),
        ),
        (
            (ReadRecoveryStep(A, "math.sum", (), "FAILED"),),
            (_rows()[0],),
        ),
    ],
    ids=[
        "missing-success",
        "reverse-dependency-append",
        "wrong-result",
        "foreign-request",
        "duplicate-receipt",
        "unstarted-receipt",
        "failed-receipt",
    ],
)
def test_rejects_mismatched_recovery_history(steps, rows):
    snapshot, retained = _snapshot(rows)
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            REQUEST, steps, snapshot, retained,
        )


def test_stale_caller_retained_tip_is_rejected():
    snapshot, _ = _snapshot()
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            REQUEST, _steps(), snapshot, genesis_witness(),
        )


def test_bool_count_is_not_a_valid_journal_witness():
    snapshot, retained = _snapshot()
    corrupted = ReadJournalWitness(True, retained.tip_sha256)
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            REQUEST, _steps(), snapshot, corrupted,
        )


def test_unresolved_started_dependency_is_rejected():
    snapshot, retained = _snapshot()
    history = (
        ReadRecoveryStep(A, "math.sum", (), "FAILED"),
        ReadRecoveryStep(B, "text.stats", (A,), "SUCCEEDED", D2),
    )
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            REQUEST, history, snapshot, retained,
        )


def test_original_journal_witness_must_remain_consistent():
    snapshot, retained = _snapshot()
    forged = replace(snapshot, witness=genesis_witness())
    with pytest.raises(ReadRecoveryJournalRejected):
        review_detached_read_journal_recovery(
            REQUEST, _steps(), forged, retained,
        )
