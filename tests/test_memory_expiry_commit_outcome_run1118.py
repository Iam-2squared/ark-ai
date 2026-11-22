"""Run1118: Memory expiry COMMIT outcome is resolved by cold SQLite readback.

Only synthetic scopes, rows and disposable local SQLite are used. A committed
expire event is not permission to erase backups or replay external effects.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


class _CommitBoundary:
    """Inject a failure immediately before or after native context-manager COMMIT."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable
        self.commit_attempts = 0
        self.native_commits = 0
        self.rollbacks = 0

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            return self.connection.__exit__(exc_type, exc, traceback)

        self.commit_attempts += 1
        if self.durable:
            self.connection.__exit__(None, None, None)
            self.native_commits += 1
        else:
            self.connection.rollback()
            self.rollbacks += 1
        raise sqlite3.OperationalError("synthetic Memory COMMIT acknowledgement lost")

    def close(self) -> None:
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize("durable", (False, True))
def test_expiry_purge_commit_outcome_requires_cold_readback_not_replay(
    tmp_path, monkeypatch, durable: bool,
) -> None:
    path = tmp_path / "memory-expiry-commit-outcome.sqlite3"
    private = MemoryScope("run1118-expiry-owner", "private")
    independent = MemoryScope("run1118-expiry-owner", "independent")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    expiring = writer.put(
        MemoryWrite(private, "expiring", "synthetic-private-fixture", expires_at_ms=199),
    )
    retained = writer.put(
        MemoryWrite(independent, "retained", "independent-fixture", expires_at_ms=500),
    )

    original_connect = writer._connect
    boundaries: list[_CommitBoundary] = []

    def uncertain_connection(*, create: bool = False):
        boundary = _CommitBoundary(
            original_connect(create=create),
            durable=durable,
        )
        boundaries.append(boundary)
        return boundary

    with monkeypatch.context() as patch:
        patch.setattr(writer, "_connect", uncertain_connection)
        with pytest.raises(
            sqlite3.OperationalError,
            match="Memory COMMIT acknowledgement lost",
        ):
            writer.purge_expired(scope=private, limit=1)

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1
    assert boundaries[0].native_commits == (1 if durable else 0)
    assert boundaries[0].rollbacks == (0 if durable else 1)

    # Cold reopen distinguishes a rolled-back sweep from a committed sweep.
    # Neither path invents an acknowledgement or automatically retries.
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    expired_after = cold.get(
        expiring.memory_id,
        private,
        include_expired=True,
    )
    retained_after = cold.get(
        retained.memory_id,
        independent,
        include_expired=True,
    )
    assert retained_after == retained

    if durable:
        assert expired_after is None
        expected_private_events = [("create", 1), ("expire", 1)]
        expected_global_events = [
            (1, expiring.memory_id, "create", 1),
            (2, retained.memory_id, "create", 1),
            (3, expiring.memory_id, "expire", 1),
        ]
    else:
        assert expired_after == expiring
        expected_private_events = [("create", 1)]
        expected_global_events = [
            (1, expiring.memory_id, "create", 1),
            (2, retained.memory_id, "create", 1),
        ]

    assert [
        (event.operation, event.revision)
        for event in cold.events(private)
    ] == expected_private_events
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT event_id,memory_id,operation,revision "
            "FROM memory_events ORDER BY event_id",
        ).fetchall() == expected_global_events
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    if durable:
        # A fresh explicit read/sweep is a no-op; it must not append a second
        # expiry event for the already committed deletion.
        assert cold.purge_expired(scope=private, limit=1) == 0
        assert [
            (event.operation, event.revision)
            for event in cold.events(private)
        ] == expected_private_events
