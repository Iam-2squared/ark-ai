"""Concurrent local audit bootstrap keeps pathname fences serialized.

Synthetic ephemeral SQLite only. No action execution, permission issuance,
trusted-clock assertion, contract migration or authenticated audit claim.
"""

import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from ark.agency import audit


def test_audit_constructor_serializes_main_and_sidecar_preflights(
    tmp_path, monkeypatch,
):
    path = tmp_path / "action-events.sqlite3"
    original = audit._require_safe_audit_path
    barrier = threading.Barrier(3)
    guard = threading.Lock()
    active = 0
    maximum = 0
    checks = 0

    def observed_preflight(candidate, *, allow_new_parents):
        nonlocal active, maximum, checks
        with guard:
            active += 1
            maximum = max(maximum, active)
            checks += 1
        try:
            time.sleep(0.02)
            return original(candidate, allow_new_parents=allow_new_parents)
        finally:
            with guard:
                active -= 1

    monkeypatch.setattr(audit, "_require_safe_audit_path", observed_preflight)

    def open_store():
        barrier.wait(timeout=10)
        return audit.SQLiteActionAudit(path, clock_ms=lambda: 100)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(open_store) for _ in range(2)]
        barrier.wait(timeout=10)
        stores = [future.result(timeout=20) for future in futures]

    assert len(stores) == 2
    assert checks >= 6
    assert maximum == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='action_events'"
        ).fetchone()[0] == 1
