"""Same-process Memory first-open preflight must share WAL bootstrap lock.

Only disposable SQLite fixtures and fixed clocks are used. This does not
claim interprocess protection or change the frozen v1 schema.
"""

import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from ark.memory import SQLiteMemoryStore
from ark.memory import sqlite_store


def test_two_initializers_serialize_precreate_path_fences(tmp_path, monkeypatch):
    path = tmp_path / "concurrent.sqlite3"
    original = sqlite_store._require_safe_memory_path
    barrier = threading.Barrier(3)
    guard = threading.Lock()
    active = 0
    maximum = 0
    checks = 0

    def observed_preflight(candidate, *, create):
        nonlocal active, maximum, checks
        if not create:
            return original(candidate, create=create)
        with guard:
            active += 1
            checks += 1
            maximum = max(maximum, active)
        try:
            # Give the competing initializer a deterministic opportunity
            # to overlap if the constructor performs checks outside the lock.
            time.sleep(0.02)
            return original(candidate, create=create)
        finally:
            with guard:
                active -= 1

    monkeypatch.setattr(
        sqlite_store, "_require_safe_memory_path", observed_preflight,
    )

    def open_store():
        barrier.wait(timeout=10)
        return SQLiteMemoryStore(path, clock_ms=lambda: 100)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(open_store) for _ in range(2)]
        barrier.wait(timeout=10)
        results = [future.result(timeout=20) for future in futures]

    assert len(results) == 2
    assert checks >= 6
    assert maximum == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='memories'"
        ).fetchone()[0] == 1
