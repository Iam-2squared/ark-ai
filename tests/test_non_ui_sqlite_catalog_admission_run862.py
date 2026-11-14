"""Bound SQL catalog admission in three disconnected/local SQLite stores.

Disposable SQLite paths only. Neither clean preflight nor rejection authenticates
a writer, approves replay, grants an action, or alters frozen v1 DDL.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import ActionAuditSchemaError, SQLiteActionAudit
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
)
from ark.memory import SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError


def _make(kind: str, path: Path):
    if kind == "memory":
        SQLiteMemoryStore(path, clock_ms=lambda: 100)
        return (
            lambda: SQLiteMemoryStore(path, clock_ms=lambda: 101),
            MemorySchemaError,
        )
    if kind == "audit":
        SQLiteActionAudit(path, clock_ms=lambda: 100)
        return (
            lambda: SQLiteActionAudit(path, clock_ms=lambda: 101),
            ActionAuditSchemaError,
        )
    policy = QuarantinePolicy(
        policy_sha256="a" * 64, first_ms=10_000,
        interval_ms=5_000, count=3, grace_ms=500,
    )
    DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    return (
        lambda: DisconnectedScheduleQuarantineLedger(path, policy=policy),
        ScheduleQuarantineRejected,
    )


@pytest.mark.parametrize("kind", ("memory", "audit", "quarantine"))
@pytest.mark.parametrize("mutation", ("many_objects", "large_ddl"))
def test_restart_preflights_catalog_before_python_ddl_hydration(
    tmp_path: Path, kind: str, mutation: str,
) -> None:
    path = tmp_path / "catalog.sqlite"
    reopen, error_type = _make(kind, path)
    # Positive control: ordinary frozen schema survives a fresh constructor.
    reopen()
    with sqlite3.connect(path) as conn:
        if mutation == "many_objects":
            for index in range(24):
                conn.execute(f"CREATE TABLE synthetic_{index}(value INTEGER)")
        else:
            # SQLite identifiers are deliberately oversized but inert. Their
            # SQL bytes must not be hydrated or normalized by Python first.
            long_name = "x" * 17_000
            conn.execute(f'CREATE TABLE synthetic ("{long_name}" INTEGER)')
    with pytest.raises(error_type, match="schema.*preflight"):
        reopen()
    assert path.is_file()


def _quarantine(tmp_path: Path):
    path = tmp_path / "quarantine.sqlite"
    policy = QuarantinePolicy(
        policy_sha256="b" * 64, first_ms=10_000,
        interval_ms=5_000, count=3, grace_ms=500,
    )
    db = DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    return path, policy, db


def test_quarantine_rejects_blob_identity_before_python_hydration(
    tmp_path: Path,
) -> None:
    path, policy, _db = _quarantine(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO quarantines VALUES(?,?,?,?,?)",
            (
                1, sqlite3.Binary(b"PRIVATE-NEVER-READ-" * 1000),
                10_000, 10_501, "c" * 64,
            ),
        )
    with pytest.raises(
        ScheduleQuarantineRejected, match="persisted storage type or width",
    ) as failure:
        DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert "PRIVATE-NEVER-READ" not in str(failure.value)
    assert path.exists()


def test_quarantine_excess_rows_refused_before_python_event_iteration(
    tmp_path: Path,
) -> None:
    path, policy, _db = _quarantine(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO quarantines VALUES(?,?,?,?,?)",
            (
                (index + 1, "slot_" + f"{index:064x}", 10_000, 10_501, "c" * 64)
                for index in range(513)
            ),
        )
    with pytest.raises(
        ScheduleQuarantineRejected, match="persisted row budget",
    ):
        DisconnectedScheduleQuarantineLedger(path, policy=policy)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (513,)
