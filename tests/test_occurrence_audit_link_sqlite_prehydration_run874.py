"""Bound disconnected occurrence and audit-link SQLite ingestion before replay.

Only disposable local fixture IDs are used. No consent, real execution or
external exactly-once outcome is implied by these synthetic DB checks.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
    _validate,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
    _replay,
)


def _fixture(tmp_path, kind):
    path = tmp_path / f"{kind}.sqlite"
    if kind == "occurrence":
        SyntheticOccurrenceStore(path)
        return path, _validate, SyntheticReplayRejected
    SyntheticOccurrenceAuditLinkStore(path)
    return path, _replay, SyntheticAuditLinkRejected


class _QuickRows:
    def __init__(self, rows):
        self.rows = rows

    def fetchmany(self, size=None):
        assert size == 2
        return self.rows

    def fetchall(self):
        raise AssertionError("unbounded SQLite diagnostic hydration")


class _BoundQuickConnection(sqlite3.Connection):
    quick_rows = [("ok",)]

    def execute(self, sql, parameters=(), /):
        if sql == "PRAGMA quick_check":
            return _QuickRows(self.quick_rows)
        return super().execute(sql, parameters)


class _BadQuickConnection(_BoundQuickConnection):
    quick_rows = [("corrupt",), ("second diagnostic",)]


@pytest.mark.parametrize("kind", ("occurrence", "audit_link"))
def test_valid_snapshot_uses_bounded_sqlite_quick_check(tmp_path, kind):
    path, review, _rejected = _fixture(tmp_path, kind)
    with sqlite3.connect(path, factory=_BoundQuickConnection) as conn:
        review(conn)


@pytest.mark.parametrize("kind", ("occurrence", "audit_link"))
def test_two_bad_diagnostics_refused_without_fetchall(tmp_path, kind):
    path, review, rejected = _fixture(tmp_path, kind)
    with sqlite3.connect(path, factory=_BadQuickConnection) as conn:
        with pytest.raises(rejected, match="quick_check|integrity"):
            review(conn)


@pytest.mark.parametrize("kind", ("occurrence", "audit_link"))
@pytest.mark.parametrize(
    "foreign_ddl", ("CREATE TABLE planted(x)", "CREATE VIEW planted AS SELECT 1"),
)
def test_unversioned_foreign_schema_denied_without_adoption(tmp_path, kind, foreign_ddl):
    path = tmp_path / f"{kind}.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(foreign_ddl)
    cls = SyntheticOccurrenceStore if kind == "occurrence" else SyntheticOccurrenceAuditLinkStore
    rejected = SyntheticReplayRejected if kind == "occurrence" else SyntheticAuditLinkRejected
    with pytest.raises(rejected, match="nonempty"):
        cls(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='planted'").fetchone()
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone() == (1,)


def _insert_oversized_row(conn, kind):
    huge = sqlite3.Binary(b"Z" * 131_072)
    if kind == "occurrence":
        conn.execute(
            """INSERT INTO synthetic_occurrence_reservations(
                 token_digest,occurrence_id,registry_revision,bound_action_id,
                 request_id,reserved_at_ms,expires_at_ms
               ) VALUES (?,?,?,?,?,?,?)""",
            (huge, "occ_" + "1" * 64, "tools_" + "2" * 64,
             "bound_" + "3" * 64, "act_" + "4" * 64, 1, 2),
        )
    else:
        conn.execute(
            """INSERT INTO synthetic_occurrence_audit_links(
                 seq,occurrence_id,registry_revision,bound_action_id,
                 request_id,audit_event_id,audit_event_digest,linked_at_ms,
                 previous_hash,link_hash
               ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (1, huge, "tools_" + "2" * 64, "bound_" + "3" * 64,
             "act_" + "4" * 64, 1, "slink_" + "5" * 64, 2,
             "slink_" + "6" * 64, "slink_" + "7" * 64),
        )


@pytest.mark.parametrize("kind", ("occurrence", "audit_link"))
def test_large_binary_identifier_denied_before_python_hydration(tmp_path, kind):
    path, review, rejected = _fixture(tmp_path, kind)
    with sqlite3.connect(path) as conn:
        _insert_oversized_row(conn, kind)
    with sqlite3.connect(path) as conn:
        statements = []
        conn.set_trace_callback(statements.append)
        with pytest.raises(rejected, match="preflight"):
            review(conn)
    assert not any(
        sql.lstrip().startswith(("SELECT token_digest", "SELECT seq,occurrence_id"))
        for sql in statements
    )
    with sqlite3.connect(path) as conn:
        table = (
            "synthetic_occurrence_reservations" if kind == "occurrence"
            else "synthetic_occurrence_audit_links"
        )
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (1,)
