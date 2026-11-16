"""SQLite catalog byte-sum preflight rejects split and multibyte identities.

In-memory writable_schema corruption is deliberately isolated. A short SQL
schema cannot justify hydrating adversarial catalog identity fields.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import planner_journal_review as planner
from ark.memory import sqlite_store as memory


@pytest.mark.parametrize("lane", ("memory", "planner"))
@pytest.mark.parametrize("shape", ("split", "utf8"))
def test_catalog_metadata_budget_is_aggregate_and_encoded(lane, shape):
    with closing(sqlite3.connect(":memory:")) as conn:
        if lane == "memory":
            for name in ("synthetic_one", "synthetic_two"):
                conn.execute(f"CREATE TABLE {name} (item TEXT)")
            maximum = 16_384
        else:
            for ddl in planner._SCHEMA:
                conn.execute(ddl)
            conn.execute("PRAGMA user_version=1")
            maximum = 4_096

        originals = [
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master ORDER BY name"
            )
        ]
        assert len(originals) == 2
        conn.execute("PRAGMA writable_schema=ON")
        if shape == "split":
            # Each individual name is below the aggregate budget; only
            # the combined catalog breaks it.
            length = 9_000 if lane == "memory" else 2_500
            for index, name in enumerate(originals):
                conn.execute(
                    "UPDATE sqlite_master SET name=? WHERE name=?",
                    (chr(65 + index) * length, name),
                )
        else:
            # Unicode codepoints are not filesystem/SQLite UTF-8 bytes.
            count = 6_000 if lane == "memory" else 1_400
            conn.execute(
                "UPDATE sqlite_master SET name=? WHERE name=?",
                ("界" * count, originals[0]),
            )
        conn.commit()

        ddl_bytes, identity_bytes, maximum_name_bytes = conn.execute(
            "SELECT SUM(length(CAST(sql AS BLOB))), "
            "SUM(length(CAST(type AS BLOB)) "
            "+ length(CAST(name AS BLOB)) "
            "+ length(CAST(tbl_name AS BLOB))), "
            "MAX(length(CAST(name AS BLOB))) FROM sqlite_master"
        ).fetchone()
        assert ddl_bytes < maximum
        assert identity_bytes > maximum
        if shape == "split":
            assert maximum_name_bytes < maximum
        else:
            # A codepoint-only cap would incorrectly admit this value.
            assert count < maximum

        if lane == "memory":
            with pytest.raises(
                memory.MemorySchemaError, match="catalog preflight budget",
            ):
                memory._schema_objects(conn)
        else:
            with pytest.raises(
                planner.SyntheticPlanJournalRejected, match="preflight budget",
            ):
                planner._schema_check(conn)
