"""Private revocation rows are bounded by SQLite before Python hydration.

Only disposable synthetic scope digests are used. A valid local privacy veto
is not independent witness custody or authenticated user consent.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    _validate,
)


class _NoRowHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT scope_digest,revoked_at_ms FROM"):
            raise AssertionError("private revocation digest hydrated before preflight")
        return super().execute(sql, parameters)


class _NoSchemaHydration(sqlite3.Connection):
    def execute(self, sql: str, parameters: tuple[object, ...] = (), /):
        if sql.startswith("SELECT type,name,tbl_name,sql FROM sqlite_master"):
            raise AssertionError("unbounded private schema hydrated before preflight")
        return super().execute(sql, parameters)


@pytest.mark.parametrize(
    "mutation",
    ("long_digest", "blob_digest", "blob_time", "negative_time"),
)
def test_reject_malformed_revocation_row_before_python_hydration(
    tmp_path: Path, mutation: str,
) -> None:
    path = tmp_path / "synthetic-revocations.sqlite3"
    ledger = SyntheticContextRevocationLedger(path)
    ledger.revoke(MemoryScope("fixture-owner", "private"), at_ms=10)

    if mutation == "long_digest":
        column, value = "scope_digest", "a" * 65
    elif mutation == "blob_digest":
        column, value = "scope_digest", sqlite3.Binary(b"a" * 64)
    elif mutation == "blob_time":
        column, value = "revoked_at_ms", sqlite3.Binary(b"\x01")
    else:
        column, value = "revoked_at_ms", -1

    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_context_revocations SET {column}=?",
            (value,),
        )

    with sqlite3.connect(path, factory=_NoRowHydration) as conn:
        with pytest.raises(
            SyntheticContextRevocationRejected,
            match="revocation row preflight",
        ):
            _validate(conn)

    with pytest.raises(SyntheticContextRevocationRejected):
        SyntheticContextRevocationLedger(path, require_existing=True)


def test_reject_excess_revocation_rows_before_hydration(tmp_path: Path) -> None:
    path = tmp_path / "many.sqlite3"
    SyntheticContextRevocationLedger(path)
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO synthetic_context_revocations VALUES(?,?)",
            ((f"{index:064x}", index) for index in range(10_001)),
        )

    with sqlite3.connect(path, factory=_NoRowHydration) as conn:
        with pytest.raises(
            SyntheticContextRevocationRejected, match="revocation row preflight",
        ):
            _validate(conn)


def test_reject_extra_sqlite_schema_before_ddl_hydration(tmp_path: Path) -> None:
    path = tmp_path / "schema.sqlite3"
    SyntheticContextRevocationLedger(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE VIEW unexpected_fixture AS SELECT 1")

    with sqlite3.connect(path, factory=_NoSchemaHydration) as conn:
        with pytest.raises(
            SyntheticContextRevocationRejected, match="revocation schema preflight",
        ):
            _validate(conn)


def test_valid_synthetic_veto_still_rejects_revoked_scope(tmp_path: Path) -> None:
    path = tmp_path / "valid.sqlite3"
    ledger = SyntheticContextRevocationLedger(path)
    revoked = MemoryScope("owner", "private")
    ledger.revoke(revoked, at_ms=10)
    reopened = SyntheticContextRevocationLedger(path, require_existing=True)
    with sqlite3.connect(path) as conn:
        _validate(conn)
    reopened.assert_not_revoked((MemoryScope("other", "private"),))
    with pytest.raises(SyntheticContextRevocationRejected, match="scope revoked"):
        reopened.assert_not_revoked((revoked,))
