"""Run1033: proactive quarantine COMMIT failure rolls back before native COMMIT."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark import disconnected_schedule_quarantine_ledger as quarantine


def _policy() -> quarantine.QuarantinePolicy:
    return quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 2, 500)


def test_precommit_failure_leaves_no_quarantine_occurrence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "quarantine-precommit-rollback.sqlite3"
    policy = _policy()
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        path,
        policy=policy,
        create=True,
    )
    retained = quarantine.genesis_quarantine_witness(policy)
    occurrence_id = quarantine.derive_quarantined_occurrence(policy, 0)

    native_connect = sqlite3.connect
    target = path.as_uri() + "?mode=rw"
    commit_attempts: list[bool] = []
    rollbacks: list[bool] = []

    class CommitFailsBeforeNative:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, *args, **kwargs):
            return self.connection.execute(*args, **kwargs)

        def commit(self) -> None:
            # Fail at the explicit COMMIT call without invoking native COMMIT.
            commit_attempts.append(True)
            raise sqlite3.OperationalError(
                "synthetic quarantine COMMIT failure before native commit",
            )

        def rollback(self) -> None:
            rollbacks.append(True)
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect(database, *args, **kwargs):
        connection = native_connect(database, *args, **kwargs)
        if database == target:
            return CommitFailsBeforeNative(connection)
        return connection

    with monkeypatch.context() as scoped:
        scoped.setattr(quarantine.sqlite3, "connect", connect)
        with pytest.raises(
            sqlite3.OperationalError,
            match="COMMIT failure before native commit",
        ):
            ledger.quarantine_expired(
                index=0,
                occurrence_id=occurrence_id,
                observed_ms=10_501,
                retained=retained,
            )

    assert commit_attempts == [True]
    assert rollbacks == [True]

    # Cold readback confirms only this synthetic local rollback outcome.
    # Quarantine remains a classification, not execution or notification.
    reopened = quarantine.DisconnectedScheduleQuarantineLedger(
        path,
        policy=policy,
    )
    assert reopened.inspect(retained=retained) == retained

    with native_connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM quarantines",
        ).fetchone() == (0,)
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
