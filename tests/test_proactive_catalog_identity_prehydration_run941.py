"""Reject oversized proactive SQLite catalog identities before Python hydration.

Only disposable in-memory SQLite writable_schema fault fixtures are used.
This does not authenticate a clock, approval, notification or real action.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark import proactive_synthetic_review as proactive


class _ForbidCatalogHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("untrusted SQLite catalog identity hydrated")
        return super().execute(sql, parameters)


def _forged_catalog() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", factory=_ForbidCatalogHydration)
    conn.execute(proactive._TABLE)
    conn.execute("PRAGMA user_version=1")
    return conn


@pytest.mark.parametrize("column", ("type", "name", "tbl_name"))
def test_unbounded_catalog_identity_refused_before_python_access(column: str) -> None:
    with closing(_forged_catalog()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? "
            "WHERE name='synthetic_prepared_triggers'",
            ("x" * 4_200,),
        )
        conn.commit()
        # The DDL budget alone is not sufficient: the identity was forged
        # independently of SQL's original bytes.
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] < 4_096
        with pytest.raises(proactive.SyntheticTriggerRejected, match="schema changed"):
            proactive._objects(conn)


def test_multibyte_catalog_identity_counts_utf8_bytes_not_characters() -> None:
    with closing(_forged_catalog()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=? "
            "WHERE name='synthetic_prepared_triggers'",
            ("山" * 1_400,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT length(name),length(CAST(name AS BLOB)) "
            "FROM sqlite_master WHERE type='table'"
        ).fetchone() == (1_400, 4_200)
        with pytest.raises(proactive.SyntheticTriggerRejected, match="schema changed"):
            proactive._objects(conn)


def test_catalog_identity_split_across_columns_remains_bounded() -> None:
    with closing(_forged_catalog()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? "
            "WHERE name='synthetic_prepared_triggers'",
            ("a" * 2_100, "b" * 2_100),
        )
        conn.commit()
        with pytest.raises(proactive.SyntheticTriggerRejected, match="schema changed"):
            proactive._objects(conn)


def test_original_proactive_sqlite_catalog_remains_admitted() -> None:
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute(proactive._TABLE)
        conn.execute("PRAGMA user_version=1")
        proactive._validate(conn)
        assert len(proactive._objects(conn)) == 2
