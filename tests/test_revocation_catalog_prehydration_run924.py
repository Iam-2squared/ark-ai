"""Revocation SQLite schema identity has a bounded prehydration gate.

Synthetic in-memory SQLite only. This does not authenticate user consent,
unrevoke a scope, query live Memory or authorize external disclosure.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.personal_context_revocation_review import (
    SyntheticContextRevocationRejected,
    _TABLE,
    _validate,
)


def _database() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(_TABLE)
    conn.execute("PRAGMA user_version=1")
    return conn


@pytest.mark.parametrize("column", ("name", "tbl_name", "type"))
@pytest.mark.parametrize("value", ("x" * 6000, "記" * 2000))
def test_revocation_catalog_identity_rejected_before_python_hydration(
    column: str, value: str,
) -> None:
    with closing(_database()) as conn:
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? "
            "WHERE name='synthetic_context_revocations'",
            (value,),
        )
        conn.execute("PRAGMA writable_schema=OFF")
        budget = conn.execute(
            "SELECT COUNT(*), "
            "COALESCE(SUM(length(CAST(sql AS BLOB))),0), "
            "COALESCE(SUM(COALESCE(length(CAST(type AS BLOB)),0) "
            "+COALESCE(length(CAST(name AS BLOB)),0) "
            "+COALESCE(length(CAST(tbl_name AS BLOB)),0)),0) "
            "FROM sqlite_master"
        ).fetchone()
        assert budget[0] == 2
        assert budget[1] < 4096
        assert budget[2] > 4096

        observed_sql: list[str] = []
        conn.set_trace_callback(observed_sql.append)
        with pytest.raises(
            SyntheticContextRevocationRejected, match="schema preflight",
        ):
            _validate(conn)
        assert not any(
            "SELECT type,name,tbl_name,sql FROM sqlite_master" in query
            for query in observed_sql
        )


def test_valid_synthetic_revocation_schema_preserves_cold_validation() -> None:
    with closing(_database()) as conn:
        assert _validate(conn) is None
