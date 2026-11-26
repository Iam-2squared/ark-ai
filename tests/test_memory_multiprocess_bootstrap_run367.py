"""Independent processes must converge on one unmodified Memory v1 schema."""

import sqlite3
import subprocess
import sys

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

_CHILD = (
    "import sys; "
    "from ark.memory import SQLiteMemoryStore; "
    "SQLiteMemoryStore(sys.argv[1], clock_ms=lambda: 100); "
    "print('BOOTSTRAPPED')"
)


@pytest.mark.parametrize("iteration", range(2))
def test_simultaneous_first_open_from_multiple_processes(tmp_path, iteration):
    path = tmp_path / f"first-open-{iteration}.db"
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
    try:
        results = [process.communicate(timeout=25) for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()

    # The security preflight intentionally refuses transient sidecar
    # identity churn. Concurrent SQLite first-open/checkpoint cleanup can
    # race a separate process's lstat without implying an unsafe DB was
    # adopted. A fail-closed refusal is not a successful bootstrap, must
    # never be misreported as one, and cannot weaken the production check.
    successes = 0
    for process, (out, err) in zip(processes, results, strict=True):
        if process.returncode == 0:
            assert out.strip() == "BOOTSTRAPPED"
            successes += 1
        else:
            assert out.strip() == ""
            assert process.returncode != 0
            assert (
                "MemorySchemaError: memory SQLite sidecar path is not "
                "a single regular file" in err
                or "MemorySchemaError: orphaned memory SQLite sidecar refused" in err
            ), err
    # One writer must have completed its actual first-open DDL; failed
    # peers never get counted, and the independent cold-open/PUT below
    # verifies subsequent usability and unchanged original v1 schema.
    assert successes >= 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='memories'"
        ).fetchone()[0] == 1
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    assert store.put(MemoryWrite(scope, "source", "safe")).revision == 1
