"""Synthetic occurrence/audit link schema checks cannot leak reference handles.

Links and fixture receipts do not prove approval, external effects or
cross-store atomicity. Only in-memory schema comparisons are exercised.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.synthetic_occurrence_audit_link_review as link


def _fixture(ddl: str = link._DDL) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl)
    conn.execute("PRAGMA user_version=1")
    return conn


def _track_oracle(monkeypatch):
    seen: list[sqlite3.Connection] = []
    original = link.closing

    def tracked(connection):
        seen.append(connection)
        return original(connection)

    monkeypatch.setattr(link, "closing", tracked)
    return seen


def _assert_closed(seen: list[sqlite3.Connection]) -> None:
    assert len(seen) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        seen[0].execute("SELECT 1")


def test_link_oracle_closes_after_empty_valid_replay(monkeypatch) -> None:
    with closing(_fixture()) as conn:
        seen = _track_oracle(monkeypatch)
        history = link._replay(conn)
        assert len(history) == 1 and history[0].event_count == 0
        _assert_closed(seen)


def test_link_oracle_closes_after_same_count_foreign_schema(
    monkeypatch,
) -> None:
    changed = link._DDL.replace(
        "linked_at_ms INTEGER NOT NULL", "linked_at_ms TEXT NOT NULL",
    )
    with closing(_fixture(changed)) as conn:
        seen = _track_oracle(monkeypatch)
        with pytest.raises(
            link.SyntheticAuditLinkRejected, match="schema changed",
        ):
            link._replay(conn)
        _assert_closed(seen)


def test_link_oracle_closes_after_injected_catalog_fault(monkeypatch) -> None:
    with closing(_fixture()) as conn:
        seen = _track_oracle(monkeypatch)

        def fail_catalog(_conn):
            raise RuntimeError("synthetic link schema read fault")

        monkeypatch.setattr(link, "_objects", fail_catalog)
        with pytest.raises(RuntimeError, match="synthetic link schema read fault"):
            link._replay(conn)
        _assert_closed(seen)
