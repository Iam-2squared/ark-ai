"""Run1459: a Personal Context revocation survives with a pinned WAL reader.

Only synthetic Memory rows and a disposable local revocation ledger are used.
The durable marker is a negative-use veto, not consent or erasure authority.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)

_OWNER = "offline-owner"
_NAMESPACE = "private"
_PRIVATE = "synthetic-private-context-run1459"


def _snapshot(connection: sqlite3.Connection) -> tuple[int]:
    return connection.execute(
        "SELECT COUNT(*) FROM synthetic_context_revocations"
    ).fetchone()


def _hard_exit_after_revoke_commit(database: str) -> None:
    ledger = SyntheticContextRevocationLedger(
        Path(database),
        require_existing=True,
    )
    native_connect = ledger._connect

    class CommitThenExit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def commit(self) -> None:
            self.connection.commit()
            # The veto row is committed; no source recheck, receipt or close.
            os._exit(81)

        def rollback(self) -> None:
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    ledger._connect = lambda *, readonly: CommitThenExit(
        native_connect(readonly=readonly),
    )
    ledger.revoke(MemoryScope(_OWNER, _NAMESPACE), at_ms=101)
    os._exit(82)


def test_revocation_commit_survives_hard_exit_with_pinned_wal_reader(
    tmp_path: Path,
) -> None:
    memory_path = tmp_path / "synthetic-memory-run1459.sqlite3"
    veto_path = tmp_path / "synthetic-context-veto-pinned-wal-run1459.sqlite3"
    scope = MemoryScope(_OWNER, _NAMESPACE)
    memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 100)
    memory.put(MemoryWrite(scope, "profile", _PRIVATE))

    ledger = SyntheticContextRevocationLedger(veto_path)
    retained = review_revocation_continuity(ledger)
    assert retained.rows == ()

    # The revocation ledger does not select WAL mode itself. Establish WAL
    # before pinning the old snapshot so the test covers WAL retention rather
    # than DELETE-journal writer exclusion.
    with closing(
        sqlite3.connect(veto_path, timeout=10, isolation_level=None)
    ) as setup:
        journal_mode = setup.execute("PRAGMA journal_mode=WAL").fetchone()
    assert journal_mode == ("wal",)

    keeper = sqlite3.connect(veto_path, timeout=10, isolation_level=None)
    keeper_open = True
    try:
        keeper.execute("PRAGMA query_only=ON")
        keeper.execute("BEGIN")
        before = (0,)
        assert _snapshot(keeper) == before

        process = multiprocessing.get_context("spawn").Process(
            target=_hard_exit_after_revoke_commit,
            args=(str(veto_path),),
        )
        process.start()
        process.join(timeout=60)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            pytest.fail("Personal Context pinned-reader worker did not terminate")
        assert process.exitcode == 81

        # The reader remains on the empty pre-revocation prefix while the
        # committed veto row is retained in WAL.
        assert _snapshot(keeper) == before
        with closing(
            sqlite3.connect(veto_path, timeout=0.2, isolation_level=None)
        ) as checkpoint_connection:
            blocked = checkpoint_connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()
        keeper_open = False

        cold = SyntheticContextRevocationLedger(
            veto_path,
            require_existing=True,
        )
        current = review_revocation_continuity(cold, retained=retained)
        assert len(current.rows) == 1
        scope_digest, revoked_at_ms = current.rows[0]
        assert type(scope_digest) is str and len(scope_digest) == 64
        assert revoked_at_ms == 101

        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            cold.assert_not_revoked((scope,))

        # The higher-level projection must observe the durable veto before
        # reading or returning the synthetic Memory content.
        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            review_fresh_nonrevoked_context(
                memory,
                CoherentSnapshotRequest(_OWNER, (_NAMESPACE,)),
                ContextSelectionPolicy(3, 3),
                cold,
                retained_revocations=retained,
            )

        with closing(sqlite3.connect(veto_path, timeout=10)) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            rows = connection.execute(
                "SELECT scope_digest,revoked_at_ms "
                "FROM synthetic_context_revocations"
            ).fetchall()
            assert rows == [current.rows[0]]
            checkpoint = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            assert checkpoint is not None
            assert checkpoint[0] == 0
            assert checkpoint[1] == checkpoint[2]

        veto_files = tuple(tmp_path.glob(veto_path.name + "*"))
        persisted_veto = b"".join(
            item.read_bytes() for item in veto_files if item.is_file()
        )
        assert _OWNER.encode("utf-8") not in persisted_veto
        assert _NAMESPACE.encode("utf-8") not in persisted_veto
        assert _PRIVATE.encode("utf-8") not in persisted_veto
    finally:
        if keeper_open:
            if keeper.in_transaction:
                keeper.rollback()
            keeper.close()
