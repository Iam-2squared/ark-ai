"""Two disconnected Python processes must serialize one Memory v1 CAS revision.

Only local temporary SQLite and Python standard-library subprocesses are used.
Neither a successful SQLite CAS nor an audit event is human authorization.
"""

import sqlite3
import subprocess
import sys
import time

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

_CHILD = r"""
import pathlib
import sys
import time

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
source = sys.argv[4]
store = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
scope = MemoryScope("offline-owner", "private")
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() > deadline:
        sys.exit("start gate timed out")
    time.sleep(0.02)
try:
    record = store.put(
        MemoryWrite(scope, "single-source", "version-from-" + source),
        expected_revision=1,
    )
except MemoryConflictError:
    print("CONFLICT", flush=True)
else:
    assert record.revision == 2
    print("SUCCESS", flush=True)
"""


@pytest.mark.parametrize("iteration", range(2))
def test_simultaneous_processes_have_one_cas_winner_and_one_audited_update(
    tmp_path, iteration,
):
    root = tmp_path / f"case-{iteration}"
    root.mkdir()
    path = root / "memory.sqlite3"
    scope = MemoryScope("offline-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    record = initial.put(MemoryWrite(scope, "single-source", "version-one"))
    gate = root / "start"
    processes = []
    for index in range(2):
        processes.append(subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(root / f"ready-{index}"), str(index),
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ))
    try:
        deadline = time.monotonic() + 25
        while not all((root / f"ready-{i}").exists() for i in range(2)):
            if any(process.poll() is not None for process in processes):
                raise AssertionError("competing process exited before CAS gate")
            if time.monotonic() >= deadline:
                raise AssertionError("competing process did not reach CAS gate")
            time.sleep(0.02)
        gate.touch()
        responses = [process.communicate(timeout=35) for process in processes]
    finally:
        gate.touch()
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert all(process.returncode == 0 for process in processes), responses
    assert sorted(output.strip() for output, _error in responses) == [
        "CONFLICT", "SUCCESS",
    ]
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT revision FROM memories WHERE memory_id=?",
            (record.memory_id,),
        ).fetchone() == (2,)
        assert conn.execute(
            "SELECT operation, revision FROM memory_events ORDER BY event_id",
        ).fetchall() == [("create", 1), ("update", 2)]
    final = initial.get(record.memory_id, scope, include_expired=True)
    assert final is not None
    assert final.content in ("version-from-0", "version-from-1")
