"""A denied post-COMMIT synthetic quarantine never implies rollback or replay.

These tests exercise genuine callbacks AFTER the SQLite COMMIT, unlike
preinstalled replacement constructors rejected before the write begins.
There is no scheduler dispatch, notification, trusted clock or real effect.
"""

import sqlite3

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    derive_quarantined_occurrence,
    genesis_quarantine_witness,
)


def _inputs(tmp_path):
    policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "quarantine.sqlite"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    return ledger, policy, path, genesis_quarantine_witness(policy)


def _advance(ledger, policy, prior):
    return ledger.quarantine_expired(
        index=0,
        occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=prior,
    )


def test_postcommit_history_tamper_blocks_receipt_but_not_committed_write(
    tmp_path, monkeypatch,
):
    ledger, policy, path, prior = _inputs(tmp_path)
    original_open = ledger._open
    witnessed_commits = []

    def tamper_on_read(*, read_only):
        if read_only:
            with sqlite3.connect(path) as conn:
                count = conn.execute(
                    "SELECT COUNT(*) FROM quarantines"
                ).fetchone()[0]
                witnessed_commits.append(count)
                conn.execute(
                    "UPDATE quarantines SET observed_ms=observed_ms+1 WHERE seq=1"
                )
        return original_open(read_only=read_only)

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "_open", tamper_on_read)
        with pytest.raises(ScheduleQuarantineRejected, match="chain altered"):
            _advance(ledger, policy, prior)

    assert witnessed_commits == [1]
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM quarantines"
        ).fetchone() == (1,)
    with pytest.raises(ScheduleQuarantineRejected, match="chain altered"):
        ledger.inspect(retained=prior)


def test_postcommit_source_epoch_drift_blocks_receipt_without_replaying(
    tmp_path, monkeypatch,
):
    ledger, policy, path, prior = _inputs(tmp_path)
    original_open = ledger._open
    original_epoch = ledger._epoch
    seen = []

    with monkeypatch.context() as patch:
        def replace_epoch_on_read(*, read_only):
            if read_only:
                with sqlite3.connect(path) as conn:
                    seen.append(conn.execute(
                        "SELECT COUNT(*) FROM quarantines"
                    ).fetchone()[0])
                patch.setattr(ledger, "_epoch", tuple(list(original_epoch)))
            return original_open(read_only=read_only)

        patch.setattr(ledger, "_open", replace_epoch_on_read)
        with pytest.raises(
            ScheduleQuarantineRejected, match="quarantine write carrier changed",
        ):
            _advance(ledger, policy, prior)

    assert seen == [1]
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM quarantines"
        ).fetchone() == (1,)
    with pytest.raises(ScheduleQuarantineRejected, match="stale"):
        ledger.inspect(retained=prior)
