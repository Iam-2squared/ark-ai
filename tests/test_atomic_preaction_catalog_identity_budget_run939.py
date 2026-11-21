"""Bound pre-action schema identity bytes before hydrating hostile catalog rows.

Disposable in-memory SQLite fault fixtures only; no action, consent or
independent audit provenance is established.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


class _NoCatalogHydration(sqlite3.Connection):
    def execute(self, sql, parameters=(), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("untrusted catalog hydrated before SQL byte admission")
        if sql == "PRAGMA quick_check":
            # Isolate the post-integrity catalog guard from SQLite's changing
            # interpretation of intentionally forged sqlite_master entries.
            return super().execute("SELECT 'ok'")
        return super().execute(sql, parameters)


def _fixture() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", factory=_NoCatalogHydration)
    conn.execute(atomic._INTENTS)
    conn.execute(atomic._AUDITS)
    conn.execute("PRAGMA user_version=1")
    return conn


@pytest.mark.parametrize("column", ("name", "tbl_name", "type"))
def test_overlong_catalog_identity_rejected_before_hydration(column: str) -> None:
    with closing(_fixture()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? WHERE name='intents'",
            ("x" * 4_200,),
        )
        conn.commit()
        count, ddl_bytes = conn.execute(
            "SELECT COUNT(*),SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert count == 4 and ddl_bytes < 4_096
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="schema catalog preflight",
        ):
            atomic._schema(conn)


def test_catalog_budget_counts_encoded_utf8_not_codepoints() -> None:
    with closing(_fixture()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=? WHERE name='intents'",
            ("山" * 1_400,),
        )
        conn.commit()
        chars, size = conn.execute(
            "SELECT length(name),length(CAST(name AS BLOB)) "
            "FROM sqlite_master WHERE type='table' LIMIT 1"
        ).fetchone()
        assert chars == 1_400 and size == 4_200
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="schema catalog preflight",
        ):
            atomic._schema(conn)


def test_split_catalog_identity_cannot_evade_cumulative_budget() -> None:
    with closing(_fixture()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            "UPDATE sqlite_master SET name=?,tbl_name=? WHERE name='intents'",
            ("a" * 2_100, "b" * 2_100),
        )
        conn.commit()
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="schema catalog preflight",
        ):
            atomic._schema(conn)


def test_pristine_catalog_still_admitted_by_schema_validator() -> None:
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute(atomic._INTENTS)
        conn.execute(atomic._AUDITS)
        conn.execute("PRAGMA user_version=1")
        atomic._schema(conn)
