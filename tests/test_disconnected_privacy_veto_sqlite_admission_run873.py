"""Disconnected privacy-veto SQLite admission before private row hydration.

These test databases are synthetic; no consent, identity or action is authorized.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.disconnected_privacy_veto as veto
from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    _inspect,
    _schema,
)


class _NoSchemaHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("schema preflight must reject before DDL hydration")
        return super().execute(sql, parameters)


class _NoRowHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT seq,owner_sha256,scope_sha256,recorded_at_ms"):
            raise AssertionError("row preflight must reject before digest hydration")
        return super().execute(sql, parameters)


class _NoFetchall(sqlite3.Cursor):
    def fetchall(self):
        raise AssertionError("quick_check must use bounded diagnostic fetch")


class _ExtraDiagnostics(sqlite3.Cursor):
    def fetchall(self):
        raise AssertionError("quick_check must use bounded diagnostic fetch")

    def fetchmany(self, size=None):
        assert size == 2
        return [("not ok",), ("additional diagnostic",)]


class _BoundedQuick(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql == "PRAGMA quick_check":
            return self.cursor(factory=_NoFetchall).execute(sql, parameters)
        return super().execute(sql, parameters)


class _BadQuick(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql == "PRAGMA quick_check":
            return self.cursor(factory=_ExtraDiagnostics).execute(sql, parameters)
        return super().execute(sql, parameters)


class _NoCatalogEnumeration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if "SELECT name FROM sqlite_master" in sql:
            raise AssertionError("unversioned catalog must use a one-row existence probe")
        return super().execute(sql, parameters)


def test_valid_veto_schema_uses_bounded_quick_check(tmp_path):
    path = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(path)
    with sqlite3.connect(path, factory=_BoundedQuick) as conn:
        _schema(conn)


def test_extra_diagnostics_cannot_be_accepted(tmp_path):
    path = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(path)
    with sqlite3.connect(path, factory=_BadQuick) as conn:
        with pytest.raises(OfflinePrivacyVetoRejected, match="integrity check"):
            _schema(conn)


@pytest.mark.parametrize("ddl", [
    "CREATE VIEW excess AS SELECT 1",
    "CREATE TABLE excess(x TEXT)",
])
def test_unversioned_foreign_db_is_not_adopted(tmp_path, ddl):
    path = tmp_path / "veto.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(ddl)
    with pytest.raises(OfflinePrivacyVetoRejected, match="unversioned veto"):
        DisconnectedPrivacyVetoLedger(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (0,)
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE name='excess'"
        ).fetchone() == ("excess",)


def test_unversioned_bootstrap_uses_one_row_catalog_probe(tmp_path, monkeypatch):
    path = tmp_path / "veto.sqlite"
    real_connect = sqlite3.connect

    def connect(database, *args, **kwargs):
        if database == path:
            kwargs["factory"] = _NoCatalogEnumeration
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(veto.sqlite3, "connect", connect)
    DisconnectedPrivacyVetoLedger(path)
    with real_connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (1,)


def test_large_foreign_schema_is_denied_before_ddl_hydration(tmp_path):
    path = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE VIEW oversize AS SELECT '" + "z" * 9_000 + "' AS value")
    with sqlite3.connect(path, factory=_NoSchemaHydration) as conn:
        with pytest.raises(OfflinePrivacyVetoRejected, match="schema preflight"):
            _schema(conn)


@pytest.mark.parametrize("mutation", ["large_text", "blob", "invalid_clock"])
def test_malformed_veto_row_is_denied_before_digest_hydration(tmp_path, mutation):
    path = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(path)
    if mutation == "large_text":
        owner, when = "a" * 9_000, 1
    elif mutation == "blob":
        owner, when = sqlite3.Binary(b"a" * 64), 1
    else:
        owner, when = "a" * 64, sqlite3.Binary(b"\\x01")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO synthetic_privacy_veto VALUES(?,?,?,?)",
            (1, owner, "b" * 64, when),
        )
    with sqlite3.connect(path, factory=_NoRowHydration) as conn:
        with pytest.raises(OfflinePrivacyVetoRejected, match="malformed"):
            _inspect(conn)


def test_513_well_formed_rows_denied_before_hydration(tmp_path):
    path = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO synthetic_privacy_veto VALUES(?,?,?,?)",
            ((i + 1, f"{i + 1:064x}", "b" * 64, i) for i in range(513)),
        )
    with sqlite3.connect(path, factory=_NoRowHydration) as conn:
        with pytest.raises(OfflinePrivacyVetoRejected, match="malformed"):
            _inspect(conn)
