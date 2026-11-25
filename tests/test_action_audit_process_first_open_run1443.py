"""Run1443: Action Audit WAL bootstrap and append across processes.

Disposable local SQLite only. No external action, trusted-time or independent
audit-custody claim is made by this synthetic concurrency fixture.
"""

from __future__ import annotations

import sqlite3
from multiprocessing import get_context
from pathlib import Path

from ark.agency import SQLiteActionAudit, ToolCall


def _audit_worker(path: str, marker: str, ready, release, results) -> None:
    ready.put("ready")
    if not release.wait(timeout=45):
        raise RuntimeError("audit bootstrap release timed out")
    audit = SQLiteActionAudit(Path(path), clock_ms=lambda: 100)
    call = ToolCall(
        "fixture.read",
        "fixture.read",
        "synthetic:scope",
        {"private_marker": marker},
    )
    event = audit.append(call, outcome="synthetic-only")
    results.put(("ok", event.event_id, event.request_id, event.outcome))


def test_two_process_first_open_and_append_converge_on_one_audit_sequence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "action-audit-process-first-open.sqlite3"
    context = get_context("spawn")
    ready = context.Queue()
    results = context.Queue()
    release = context.Event()
    markers = ("private-writer-a-run1443", "private-writer-b-run1443")
    processes = [
        context.Process(
            target=_audit_worker,
            args=(str(path), marker, ready, release, results),
        )
        for marker in markers
    ]
    try:
        for process in processes:
            process.start()
        assert [ready.get(timeout=60) for _ in processes] == ["ready", "ready"]
        release.set()
        outcomes = [results.get(timeout=60) for _ in processes]
        for process in processes:
            process.join(timeout=60)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        assert [process.exitcode for process in processes] == [0, 0]
    finally:
        release.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        ready.close()
        results.close()

    assert [outcome[0] for outcome in outcomes] == ["ok", "ok"]
    assert sorted(outcome[1] for outcome in outcomes) == [1, 2]
    assert len({outcome[2] for outcome in outcomes}) == 2
    assert all(outcome[3] == "synthetic-only" for outcome in outcomes)

    cold = SQLiteActionAudit(path, clock_ms=lambda: 101)
    events = cold.events()
    assert [event.event_id for event in events] == [1, 2]
    assert len({event.request_id for event in events}) == 2
    assert [event.occurred_at_ms for event in events] == [100, 100]
    assert all(event.outcome == "synthetic-only" for event in events)

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute(
            "SELECT COUNT(*) FROM action_events"
        ).fetchone() == (2,)

    database_bytes = path.read_bytes()
    assert all(marker.encode("utf-8") not in database_bytes for marker in markers)
