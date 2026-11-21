"""Synthetic occurrence reservation catalog preflight must bound identity bytes.

No one-shot token, grant, trusted clock, backend execution, external effect or
replay decision is conferred by these disposable SQLite catalog fixtures.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import durable_occurrence_review as occurrence


class _NoCatalogHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("occurrence catalog hydrated before SQLite budget")
        return super().execute(sql, parameters)


@pytest.mark.parametrize("field", ("type", "name", "tbl_name"))
def test_persisted_occurrence_catalog_identity_refused_before_hydration(field):
    with closing(sqlite3.connect(":memory:", factory=_NoCatalogHydration)) as conn:
        conn.execute(occurrence._TABLE)
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {field}=? WHERE type='table'",
            ("x" * 8_193,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] == 3
        with pytest.raises(occurrence.SyntheticReplayRejected, match="schema changed"):
            occurrence._objects(conn)


def test_utf8_occurrence_catalog_bytes_not_characters_are_bounded():
    with closing(sqlite3.connect(":memory:", factory=_NoCatalogHydration)) as conn:
        conn.execute(occurrence._TABLE)
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=? WHERE type='table'",
            ("山" * 2_750,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT length(name), length(CAST(name AS BLOB)) "
            "FROM sqlite_master WHERE type='table'"
        ).fetchone() == (2_750, 8_250)
        with pytest.raises(occurrence.SyntheticReplayRejected, match="schema changed"):
            occurrence._objects(conn)


def test_cumulative_occurrence_catalog_name_budget():
    with closing(sqlite3.connect(":memory:", factory=_NoCatalogHydration)) as conn:
        conn.execute(occurrence._TABLE)
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?, tbl_name=? WHERE type='table'",
            ("x" * 4_100, "y" * 4_100),
        )
        conn.commit()
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] < 8_192
        with pytest.raises(occurrence.SyntheticReplayRejected, match="schema changed"):
            occurrence._objects(conn)


def test_original_occurrence_catalog_matches_frozen_local_ddl():
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute(occurrence._TABLE)
        conn.execute("PRAGMA user_version=1")
        assert len(occurrence._objects(conn)) == 3
        occurrence._validate(conn)
