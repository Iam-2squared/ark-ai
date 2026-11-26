"""Bound disposable Planner sqlite_master identity metadata before hydration.

No physical machine, live tool, protected evaluation or external effect.
"""

import sqlite3
from contextlib import closing

import pytest

from ark.agency import planner_journal_review as journal


def _synthetic_schema(conn):
    for ddl in journal._SCHEMA:
        conn.execute(ddl)
    conn.execute("PRAGMA user_version=1")


@pytest.mark.parametrize("column", ("name", "tbl_name", "type"))
def test_planner_sql_catalog_identity_preflight_blocks_huge_metadata(column):
    with closing(sqlite3.connect(":memory:")) as conn:
        _synthetic_schema(conn)
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? "
            "WHERE name='synthetic_plan_header'",
            ("X" * 4_097,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
            "FROM sqlite_master"
        ).fetchone()[0] < 4_096
        with pytest.raises(
            journal.SyntheticPlanJournalRejected,
            match="preflight budget exceeded",
        ):
            journal._schema_check(conn)


def test_standard_synthetic_journal_schema_passes_catalog_admission():
    with closing(sqlite3.connect(":memory:")) as conn:
        _synthetic_schema(conn)
        journal._schema_check(conn)
