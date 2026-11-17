"""Concurrent WAL reader, cold writer and last-close evidence on disposable Memory.

The external process reads a pinned SQLite snapshot; local Memory must still
commit an atomic row/event update, persist it after the reader closes, and
reject a stale generation token. No private user DB, authority, or dispatch.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time

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

path = pathlib.Path(sys.argv[1])
ready = pathlib.Path(sys.argv[2])
written = pathlib.Path(sys.argv[3])
observed = pathlib.Path(sys.argv[4])
release = pathlib.Path(sys.argv[5])
mode = sys.argv[6]
target = path.as_uri() + "?mode=ro" if mode == "ro" else str(path)
connection = sqlite3.connect(target, uri=mode == "ro", timeout=10, isolation_level=None)
connection.execute("BEGIN")

def snapshot():
    row = connection.execute(
        "SELECT revision FROM memories WHERE owner_id=? AND namespace=?",
        ("synthetic-reader-owner", "private"),
    ).fetchone()
    events = connection.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
    return row[0], events

assert snapshot() == (1, 1)
ready.touch()
deadline = time.monotonic() + 25
while not written.exists():
    if time.monotonic() >= deadline:
        sys.exit("writer did not signal")
    time.sleep(0.02)
assert snapshot() == (1, 1)
# Publish a completed payload, not merely a created-but-empty file. The
# parent waits on existence before reading the marker; direct write_text
# exposes an empty file transiently on slower Windows/CI filesystems.
pending = observed.with_name(observed.name + ".pending")
pending.write_text("old-snapshot", encoding="ascii")
pending.replace(observed)
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit("release did not arrive")
    time.sleep(0.02)
connection.rollback()
connection.close()
"""


def _await_marker(path, process) -> None:
    deadline = time.monotonic() + 25
    while not path.exists():
        if process.poll() is not None:
            raise AssertionError("SQLite reader exited before its barrier")
        if time.monotonic() >= deadline:
            raise AssertionError("SQLite reader barrier timed out")
        time.sleep(0.02)


@pytest.mark.parametrize("reader_mode", ("ro", "rw"))
def test_cold_memory_writer_survives_reader_and_last_close(tmp_path, reader_mode):
    path = tmp_path / "cross-process-memory.sqlite3"
    scope = MemoryScope("synthetic-reader-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    saved = initial.put(MemoryWrite(scope, "same", "initial"))
    token = observe_memory_generation_for_cas(initial, scope, "same")
    ready = tmp_path / "reader-ready"
    written = tmp_path / "writer-done"
    observed = tmp_path / "reader-observed"
    release = tmp_path / "release-reader"
    process = subprocess.Popen(
        [sys.executable, "-c", _CHILD, str(path), str(ready), str(written),
         str(observed), str(release), reader_mode],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        _await_marker(ready, process)
        # SQLite WAL permits the second writer to atomically advance the
        # current row/event while an independent old reader is still pinned.
        writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
        changed = generation_fenced_memory_update(
            writer, MemoryWrite(scope, "same", "updated"), retained=token,
        )
        assert changed.revision == 2
        written.touch()
        _await_marker(observed, process)
        assert observed.read_text(encoding="ascii") == "old-snapshot"

        cold = SQLiteMemoryStore(path, clock_ms=lambda: 300)
        assert cold.get(saved.memory_id, scope) == changed
        assert [(e.event_id, e.operation, e.revision) for e in cold.events(scope)] == [
            (1, "create", 1), (2, "update", 2),
        ]
        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                cold, MemoryWrite(scope, "same", "forbidden replay"),
                retained=token,
            )
    finally:
        release.touch()
        if process.poll() is None:
            try:
                process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
        else:
            process.communicate()
    assert process.returncode == 0

    # The final SQLite reader-close/checkpoint lifecycle must not erase the
    # committed row/event pair or refresh a stale replay generation.
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 400)
    assert reopened.get(saved.memory_id, scope) == changed
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (2,)
