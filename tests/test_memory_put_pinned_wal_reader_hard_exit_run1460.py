"""Run1460: Memory put row/event COMMIT survives with a pinned WAL reader."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
from contextlib import closing
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryConflictError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore

_BEFORE = "synthetic-memory-before-run1460"
_AFTER = "synthetic-memory-after-run1460"
_STALE = "synthetic-memory-stale-retry-run1460"


def _scope() -> MemoryScope:
    return MemoryScope("synthetic-owner", "private")


def _write(content: str) -> MemoryWrite:
    return MemoryWrite(_scope(), "profile", content, {"kind": "fixture"})


def _snapshot(connection: sqlite3.Connection, memory_id: str):
    row = connection.execute(
        """SELECT memory_id,owner_id,namespace,source_id,content,content_sha256,
                  created_at_ms,updated_at_ms,expires_at_ms,revision
           FROM memories WHERE memory_id=?""",
        (memory_id,),
    ).fetchone()
    events = connection.execute(
        """SELECT event_id,memory_id,owner_id,namespace,operation,revision,occurred_at_ms
           FROM memory_events WHERE memory_id=? ORDER BY event_id""",
        (memory_id,),
    ).fetchall()
    return row, events


def _exit_after_native_commit(database: str) -> None:
    store = SQLiteMemoryStore(Path(database), clock_ms=lambda: 200)
    put_code = SQLiteMemoryStore.put.__code__

    def exit_after_commit(frame, event, argument) -> None:
        if (
            event == "c_return"
            and frame.f_code is put_code
            and getattr(argument, "__name__", None) == "__exit__"
            and type(getattr(argument, "__self__", None)) is sqlite3.Connection
            and not argument.__self__.in_transaction
        ):
            # The row and event are committed; no receipt or post-COMMIT
            # MemoryRecord construction/checks may run in this child.
            os._exit(74)

    sys.setprofile(exit_after_commit)
    store.put(_write(_AFTER), expected_revision=1)
    os._exit(75)


def test_memory_put_commit_survives_hard_exit_with_pinned_wal_reader(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory-put-pinned-wal-reader-run1460.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    initial = store.put(_write(_BEFORE), expected_revision=0)
    assert initial.revision == 1

    with closing(sqlite3.connect(path, timeout=10, isolation_level=None)) as setup:
        assert setup.execute("PRAGMA journal_mode").fetchone() == ("wal",)

    keeper = sqlite3.connect(path, timeout=10, isolation_level=None)
    keeper_open = True
    try:
        keeper.execute("PRAGMA query_only=ON")
        keeper.execute("BEGIN")
        before = _snapshot(keeper, initial.memory_id)
        assert before[0] is not None
        assert before[0][4] == _BEFORE
        assert before[0][9] == 1
        assert [
            (event[0], event[4], event[5], event[6]) for event in before[1]
        ] == [(1, "create", 1, 100)]

        process = get_context("spawn").Process(
            target=_exit_after_native_commit,
            args=(str(path),),
        )
        process.start()
        process.join(timeout=60)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            pytest.fail("Memory put pinned-reader worker did not terminate")
        assert process.exitcode == 74

        # The old reader must retain the revision-1 row and create-event
        # prefix while revision 2 and its update event are committed in WAL.
        assert _snapshot(keeper, initial.memory_id) == before
        with closing(
            sqlite3.connect(path, timeout=0.2, isolation_level=None)
        ) as checkpoint_connection:
            blocked = checkpoint_connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()
        keeper_open = False

        cold = SQLiteMemoryStore(path, clock_ms=lambda: 300)
        recovered = cold.get(initial.memory_id, _scope())
        assert recovered is not None
        assert recovered.memory_id == initial.memory_id
        assert recovered.content == _AFTER
        assert recovered.content_sha256 == hashlib.sha256(
            _AFTER.encode("utf-8")
        ).hexdigest()
        assert recovered.created_at_ms == 100
        assert recovered.updated_at_ms == 200
        assert recovered.revision == 2
        assert dict(recovered.metadata) == {"kind": "fixture"}

        # A lost caller receipt cannot justify replaying the stale revision-1
        # CAS. The durable row/event pair remains exactly one update ahead.
        with pytest.raises(MemoryConflictError):
            cold.put(_write(_STALE), expected_revision=1)
        reread = cold.get(initial.memory_id, _scope())
        assert reread is not None
        assert reread.content == _AFTER
        assert reread.revision == 2
        events = cold.events(_scope())
        matching = [event for event in events if event.memory_id == initial.memory_id]
        assert [
            (event.event_id, event.operation, event.revision, event.occurred_at_ms)
            for event in matching
        ] == [(1, "create", 1, 100), (2, "update", 2, 200)]
        assert _BEFORE not in repr(matching)
        assert _AFTER not in repr(matching)
        assert _STALE not in repr(matching)

        with closing(sqlite3.connect(path, timeout=10)) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            columns = [
                row[1]
                for row in connection.execute("PRAGMA table_info(memory_events)")
            ]
            assert columns == [
                "event_id",
                "memory_id",
                "owner_id",
                "namespace",
                "operation",
                "revision",
                "occurred_at_ms",
            ]
            assert connection.execute(
                """SELECT operation,revision,occurred_at_ms
                   FROM memory_events WHERE memory_id=? ORDER BY event_id""",
                (initial.memory_id,),
            ).fetchall() == [
                ("create", 1, 100),
                ("update", 2, 200),
            ]
            checkpoint = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            assert checkpoint is not None
            assert checkpoint[0] == 0
            assert checkpoint[1] == checkpoint[2]
    finally:
        if keeper_open:
            if keeper.in_transaction:
                keeper.rollback()
            keeper.close()
