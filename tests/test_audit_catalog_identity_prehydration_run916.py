"""Audit catalog admission bounds stored identities, not only schema DDL.

No real audited action, credential, trusted clock, or external effect is used.
All hostile catalogs are disposable SQLite :memory: fault fixtures.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import audit


class _RefuseHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("audit schema hydrated before SQLite preflight")
        return super().execute(sql, parameters)


@pytest.mark.parametrize("field", ("name", "tbl_name", "type"))
def test_audit_catalog_metadata_rejected_before_python_hydration(field):
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        conn.execute("CREATE TABLE fixture (item TEXT)")
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? WHERE name='fixture'",
            ("a" * 16_385,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] < 16_384
        with pytest.raises(audit.ActionAuditSchemaError, match="catalog preflight"):
            audit._schema_objects(conn)


def test_audit_metadata_budget_is_utf8_bytes_not_character_length():
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        conn.execute("CREATE TABLE fixture (item TEXT)")
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=? WHERE name='fixture'",
            ("山" * 5_500,),
        )
        conn.commit()
        chars, byte_length = conn.execute(
            "SELECT length(name),length(CAST(name AS BLOB)) FROM sqlite_master"
        ).fetchone()
        assert chars == 5_500 and byte_length == 16_500
        with pytest.raises(audit.ActionAuditSchemaError, match="catalog preflight"):
            audit._schema_objects(conn)


def test_audit_cumulative_catalog_identity_budget_refuses_split_fields():
    with closing(sqlite3.connect(":memory:", factory=_RefuseHydration)) as conn:
        conn.execute("CREATE TABLE fixture (item TEXT)")
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? WHERE name='fixture'",
            ("a" * 8_200, "b" * 8_200),
        )
        conn.commit()
        with pytest.raises(audit.ActionAuditSchemaError, match="catalog preflight"):
            audit._schema_objects(conn)


def test_audit_small_normal_catalog_remains_admitted():
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE fixture (item TEXT)")
        entries = audit._schema_objects(conn)
        assert len(entries) == 1
        assert entries[0][0:3] == ("table", "fixture", "fixture")
