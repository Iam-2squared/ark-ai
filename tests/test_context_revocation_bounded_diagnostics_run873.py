"""Bound synthetic revocation SQLite diagnostics and bootstrap admission.

Disposable fixture only; no authenticated consent, deletion or external effects.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.personal_context_revocation_review as revocation
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    _validate,
)


class _NoUnboundedQuick(sqlite3.Cursor):
    def fetchall(self):
        raise AssertionError("quick_check must not hydrate an unbounded result")


class _QuickCursor(sqlite3.Cursor):
    def fetchall(self):
        raise AssertionError("quick_check must not hydrate an unbounded result")

    def fetchmany(self, size=None):
        assert size == 2
        return [("not ok",), ("second diagnostic",)]


class _BoundedDiagnosticConnection(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql == "PRAGMA quick_check":
            return self.cursor(factory=_NoUnboundedQuick).execute(sql, parameters)
        return super().execute(sql, parameters)


class _BadDiagnosticConnection(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql == "PRAGMA quick_check":
            return self.cursor(factory=_QuickCursor).execute(sql, parameters)
        return super().execute(sql, parameters)


class _NoCatalogEnumeration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if "SELECT name FROM sqlite_master" in sql:
            raise AssertionError("unversioned schema must use one-row existence probe")
        return super().execute(sql, parameters)


def test_valid_existing_revocation_db_uses_bounded_sqlite_diagnostic(tmp_path):
    path = tmp_path / "revocation.sqlite"
    SyntheticContextRevocationLedger(path)
    with sqlite3.connect(path, factory=_BoundedDiagnosticConnection) as conn:
        _validate(conn)


def test_two_bad_diagnostics_are_rejected_without_fetchall(tmp_path):
    path = tmp_path / "revocation.sqlite"
    SyntheticContextRevocationLedger(path)
    with sqlite3.connect(path, factory=_BadDiagnosticConnection) as conn:
        with pytest.raises(SyntheticContextRevocationRejected, match="quick_check"):
            _validate(conn)


def test_bootstrap_uses_one_row_catalog_probe_before_schema_creation(tmp_path, monkeypatch):
    path = tmp_path / "revocation.sqlite"
    original_connect = sqlite3.connect

    def guarded_connect(database, *args, **kwargs):
        if database == path:
            kwargs["factory"] = _NoCatalogEnumeration
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(revocation.sqlite3, "connect", guarded_connect)
    SyntheticContextRevocationLedger(path)
    with original_connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (1,)


@pytest.mark.parametrize(
    "foreign_ddl",
    ("CREATE TABLE injected(x TEXT)", "CREATE VIEW injected AS SELECT 1"),
)
def test_foreign_unversioned_schema_rejected_without_repair(tmp_path, foreign_ddl):
    path = tmp_path / "revocation.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(foreign_ddl)
    with pytest.raises(
        SyntheticContextRevocationRejected, match="unversioned revocation",
    ):
        SyntheticContextRevocationLedger(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='injected'"
        ).fetchone() == ("injected",)
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='synthetic_context_revocations'"
        ).fetchone() is None
