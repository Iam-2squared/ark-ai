"""Audit WAL mode is bootstrapped once, even with concurrent openers."""

import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from ark.agency import SQLiteActionAudit

_CHILD = (
    "import sys; "
    "from ark.agency import SQLiteActionAudit; "
    "SQLiteActionAudit(sys.argv[1], clock_ms=lambda: 100); "
    "print('BOOTSTRAPPED')"
)


def test_routine_connection_does_not_renegotiate_wal_during_writer_lock(tmp_path):
    path = tmp_path / "action-audit.db"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 10)
    with sqlite3.connect(path) as writer:
        writer.execute("BEGIN IMMEDIATE")
        with audit._connect() as reader:
            assert reader.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert reader.execute("PRAGMA user_version").fetchone()[0] == 1
        writer.rollback()


def test_two_thread_initializers_preserve_exact_v1_schema(tmp_path):
    path = tmp_path / "concurrent-audit.db"

    def initialize(_index: int) -> bool:
        SQLiteActionAudit(path, clock_ms=lambda: 100)
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(initialize, (0, 1))) == [True, True]
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


@pytest.mark.parametrize("iteration", range(2))
def test_independent_first_open_processes_converge(tmp_path, iteration):
    path = tmp_path / f"process-{iteration}.db"
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
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    assert audit.events() == []
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
