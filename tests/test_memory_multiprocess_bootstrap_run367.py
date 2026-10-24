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

    for process, (out, err) in zip(processes, results, strict=True):
        assert process.returncode == 0, err
        assert out.strip() == "BOOTSTRAPPED"
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='memories'"
        ).fetchone()[0] == 1
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    assert store.put(MemoryWrite(scope, "source", "safe")).revision == 1
