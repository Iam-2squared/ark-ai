"""Scoped expiry survives an independent pinned WAL reader and last close.

All rows and processes are disposable. A local expiry decision is not
authenticated retention authority, erasure consent or external execution.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from contextlib import closing

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_CHILD = r"""
import pathlib
import sqlite3
import sys
import time

path, ready, written, observed, release = map(pathlib.Path, sys.argv[1:6])
mode = sys.argv[6]
db = path.as_uri() + "?mode=ro" if mode == "ro" else str(path)
conn = sqlite3.connect(db, uri=mode == "ro", isolation_level=None, timeout=10)
conn.execute("BEGIN")

def snapshot():
    row = conn.execute(
        "SELECT COUNT(*) FROM memories WHERE owner_id=? AND namespace=?",
        ("synthetic-expiring-owner", "private"),
    ).fetchone()[0]
    all_events = conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
    return row, all_events

assert snapshot() == (1, 2)
ready.touch()
deadline = time.monotonic() + 25
while not written.exists():
    if time.monotonic() >= deadline:
        sys.exit("expiry writer never signaled")
    time.sleep(0.02)
assert snapshot() == (1, 2)
# Publish the completed marker atomically: touch/existence is not a content barrier.
# A non-atomic write_text creates an empty file before writing, which makes
# parent-side exists() checks intermittently observe an empty marker on CI.
pending = observed.with_name(observed.name + ".pending")
pending.write_text("pinned-old-snapshot", encoding="ascii")
pending.replace(observed)
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit("reader release never signaled")
    time.sleep(0.02)
conn.rollback()
conn.close()
"""


def _barrier(marker, child) -> None:
    deadline = time.monotonic() + 25
    while not marker.exists():
        if child.poll() is not None:
            raise AssertionError("WAL child died before marker")
        if time.monotonic() >= deadline:
            raise AssertionError("WAL child barrier expired")
        time.sleep(0.02)


@pytest.mark.parametrize("reader_mode", ("ro", "rw"))
@pytest.mark.parametrize("foreign_owner", (False, True))
def test_scoped_expiry_and_generation_survive_pinned_reader_last_close(
    tmp_path, reader_mode: str, foreign_owner: bool,
) -> None:
    path = tmp_path / "scoped-wal-expiry.sqlite3"
    own = MemoryScope("synthetic-expiring-owner", "private")
    foreign = (
        MemoryScope("synthetic-foreign-owner", "private") if foreign_owner
        else MemoryScope("synthetic-expiring-owner", "unrelated")
    )
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    due = initial.put(MemoryWrite(own, "due", "private-content", expires_at_ms=150))
    other = initial.put(
        MemoryWrite(foreign, "foreign", "unrelated-content", expires_at_ms=150)
    )
    token = observe_memory_generation_for_cas(initial, own, "due")
    ready, written, observed, release = (
        tmp_path / name
        for name in ("ready", "written", "observed", "release")
    )
    child = subprocess.Popen(
        [sys.executable, "-c", _CHILD, str(path), str(ready), str(written),
         str(observed), str(release), reader_mode],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _barrier(ready, child)
        writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
        assert writer.purge_expired(scope=own, limit=1) == 1
        written.touch()
        _barrier(observed, child)
        assert observed.read_text(encoding="ascii") == "pinned-old-snapshot"

        cold = SQLiteMemoryStore(path, clock_ms=lambda: 201)
        assert cold.get(due.memory_id, own, include_expired=True) is None
        assert cold.get(other.memory_id, foreign, include_expired=True) == other
        assert [event.operation for event in cold.events(own)] == [
            "create", "expire",
        ]
        assert [event.operation for event in cold.events(foreign)] == ["create"]
        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                cold, MemoryWrite(own, "due", "cannot-replay"),
                retained=token,
            )
    finally:
        release.touch()
        try:
            child.communicate(timeout=35)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
    assert child.returncode == 0

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 202)
    assert reopened.get(due.memory_id, own, include_expired=True) is None
    assert reopened.get(other.memory_id, foreign, include_expired=True) == other
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (3,)
