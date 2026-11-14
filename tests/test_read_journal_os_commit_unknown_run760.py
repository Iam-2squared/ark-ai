"""Cold READ-journal recovery across an actual process COMMIT/exit boundary.

All receipts are disconnected synthetic digests. An unseen committed append
must be reconciled from independently retained evidence, never auto-replayed.
"""

from __future__ import annotations

import os
import sqlite3
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)


def _row(number: int) -> ReadReceipt:
    return ReadReceipt(
        "req_" + "a" * 32,
        "step_" + f"{number:016x}",
        "math.sum",
        "b" * 64,
        "c" * 64,
    )


def _abrupt_read_append(path: str, stage: str, prior: ReadJournalWitness) -> None:
    if stage == "postcommit_no_reply":
        with DisconnectedReadJournal.open(Path(path)) as journal:
            journal.append(_row(2), prior)
            os._exit(0)  # COMMIT occurred, result not retained by caller.
    if stage == "precommit_unreplied":
        conn = sqlite3.connect(path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        next_tip = _chain(prior.tip_sha256, 2, _row(2))
        conn.execute(
            "INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?)",
            (
                2, _row(2).request_id, _row(2).step_id, _row(2).operation,
                _row(2).input_digest, _row(2).result_digest,
                prior.tip_sha256, next_tip,
            ),
        )
        os._exit(0)  # No COMMIT, rollback handler or result.
    os._exit(92)


@pytest.mark.parametrize("stage", ("precommit_unreplied", "postcommit_no_reply"))
def test_read_journal_cold_commit_unknown_is_not_a_replay_grant(tmp_path, stage):
    path = tmp_path / "synthetic-read-commit-unknown.sqlite3"
    with DisconnectedReadJournal.create(path) as journal:
        first_tip = journal.append(_row(1), genesis_witness())

    child = get_context("spawn").Process(
        target=_abrupt_read_append,
        args=(str(path), stage, first_tip),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    with DisconnectedReadJournal.open(path) as cold:
        if stage == "precommit_unreplied":
            snapshot = cold.recover_receipts(first_tip)
            assert snapshot.receipts == (_row(1),)
            assert cold.verify(first_tip) == first_tip
        else:
            second_tip = ReadJournalWitness(
                2, _chain(first_tip.tip_sha256, 2, _row(2)),
            )
            with pytest.raises(ReadJournalRejected, match="external witness"):
                cold.verify(first_tip)
            snapshot = cold.recover_receipts(second_tip)
            assert snapshot.witness == second_tip
            assert snapshot.receipts == (_row(1), _row(2))
            # A committed but unacknowledged append cannot be tried again
            # with the old witness, even with a different synthetic step.
            with pytest.raises(ReadJournalRejected, match="stale"):
                cold.append(_row(3), first_tip)

        assert snapshot.dispatch_authorized is False
        assert snapshot.effect_proven is False
        assert snapshot.automatic_replay_authorized is False
        assert snapshot.independent_custody_proven is False
