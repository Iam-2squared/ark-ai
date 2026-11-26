"""ActionAudit's in-memory DDL oracle is closed on every verification path.

Fixtures use a temporary local audit store. No real tool or external action
is dispatched; a valid local event is not proof of authorized execution.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.agency.audit as audit_module
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _track_memory_connections(monkeypatch):
    opened: list[sqlite3.Connection] = []
    closed: list[sqlite3.Connection] = []
    original_connect = sqlite3.connect

    class TrackedMemoryConnection(sqlite3.Connection):
        def close(self):
            closed.append(self)
            return super().close()

    def connect(database, *args, **kwargs):
        if database == ":memory:":
            assert "factory" not in kwargs
            kwargs["factory"] = TrackedMemoryConnection
            instance = original_connect(database, *args, **kwargs)
            opened.append(instance)
            return instance
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(audit_module.sqlite3, "connect", connect)
    return opened, closed


def _call() -> ToolCall:
    return ToolCall("fixture", "fixture.read", "local", {"synthetic": True})


def test_audit_oracle_closes_after_bootstrap_append_and_reopen(
    tmp_path: Path, monkeypatch,
) -> None:
    opened, closed = _track_memory_connections(monkeypatch)
    path = tmp_path / "audit.sqlite"
    audit = audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
    for _ in range(2):
        audit.append(_call(), outcome="synthetic-only")
    recovered = audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
    assert len(recovered.events()) == 2
    assert len(opened) >= 3
    assert len(opened) == len(closed)
    assert all(a is b for a, b in zip(opened, closed, strict=True))


def test_audit_oracle_closes_after_foreign_schema_refusal(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "audit.sqlite"
    audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE INDEX other_index ON action_events(scope)")
    opened, closed = _track_memory_connections(monkeypatch)
    with pytest.raises(ActionAuditSchemaError, match="schema differs"):
        audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
    assert len(opened) == len(closed) == 1
    assert opened[0] is closed[0]


def test_audit_oracle_closes_if_catalog_inspection_raises(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "audit.sqlite"
    audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
    opened, closed = _track_memory_connections(monkeypatch)

    def inject_fault(_conn):
        raise RuntimeError("synthetic catalog inspection fault")

    monkeypatch.setattr(audit_module, "_schema_objects", inject_fault)
    with pytest.raises(RuntimeError, match="synthetic catalog inspection fault"):
        audit_module.SQLiteActionAudit(path, clock_ms=lambda: 100)
    assert len(opened) == len(closed) == 1
    assert opened[0] is closed[0]
