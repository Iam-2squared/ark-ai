"""Bound synthetic Memory sqlite_master metadata before Python hydration.

No user database, private Memory content, migration or destructive operation.
The fixture uses only disposable in-memory SQLite catalog fault injection.
"""

from contextlib import closing
import sqlite3

import pytest

from ark.memory import sqlite_store


@pytest.mark.parametrize("column", ("name", "tbl_name", "type"))
def test_catalog_identity_byte_budget_refuses_oversized_stored_metadata(column):
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE synthetic (value TEXT)")
        conn.execute("PRAGMA writable_schema=ON")
        # SQLite schema metadata is intentionally malformed in this *local*
        # in-memory fixture; sql stays short, so the DDL-only budget passes.
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? WHERE name='synthetic'",
            ("x" * 16_385,),
        )
        conn.commit()
        assert conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))) FROM sqlite_master"
        ).fetchone()[0] < 16_384
        with pytest.raises(
            sqlite_store.MemorySchemaError, match="catalog preflight budget exceeded",
        ):
            sqlite_store._schema_objects(conn)


def test_normal_catalog_metadata_still_hydrates_for_schema_comparison():
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE synthetic (value TEXT)")
        rows = sqlite_store._schema_objects(conn)
        assert len(rows) == 1
        assert rows[0][0:3] == ("table", "synthetic", "synthetic")
