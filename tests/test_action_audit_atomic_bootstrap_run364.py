"""Synthetic ActionAudit v1 bootstrap must preserve foreign and partial state."""

import sqlite3

import pytest

from ark.agency import ActionAuditSchemaError, SQLiteActionAudit, ToolCall


def test_new_database_initializes_atomically_and_reopens(tmp_path):
    path = tmp_path / "audit.sqlite3"
    first = SQLiteActionAudit(path, clock_ms=lambda: 100)
    call = ToolCall("fixture.read", "fixture.read", "synthetic:scope")
    event = first.append(call, outcome="synthetic-only")
    second = SQLiteActionAudit(path, clock_ms=lambda: 101)
    assert second.events() == [event]
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1


@pytest.mark.parametrize("kind", ("foreign", "partial"))
def test_unversioned_preexisting_tables_fail_without_repair(tmp_path, kind):
    path = tmp_path / "audit.sqlite3"
    name = "foreign_data" if kind == "foreign" else "action_events"
    with sqlite3.connect(path) as conn:
        conn.execute(f"CREATE TABLE {name}(payload TEXT NOT NULL)")
        conn.execute(f"INSERT INTO {name}(payload) VALUES ('keep')")
    with pytest.raises(ActionAuditSchemaError, match="not empty"):
        SQLiteActionAudit(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(f"SELECT payload FROM {name}").fetchall() == [("keep",)]
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='idx_action_request'"
        ).fetchone()[0] == 0


def test_negative_user_version_fails_closed_without_repair(tmp_path):
    path = tmp_path / "audit.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=-1")
    with pytest.raises(ActionAuditSchemaError, match="unsupported"):
        SQLiteActionAudit(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == -1
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='action_events'"
        ).fetchone()[0] == 0


def test_failed_post_create_validation_rolls_back_all_bootstrap(tmp_path, monkeypatch):
    path = tmp_path / "audit.sqlite3"

    def failing_validation(_conn):
        raise ActionAuditSchemaError("synthetic verification failure")

    monkeypatch.setattr("ark.agency.audit._validate_v1_schema", failing_validation)
    with pytest.raises(ActionAuditSchemaError, match="synthetic verification"):
        SQLiteActionAudit(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE name IN ('action_events','idx_action_request')"
        ).fetchone()[0] == 0
