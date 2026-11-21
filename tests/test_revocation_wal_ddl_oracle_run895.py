"""Independent v1 DDL oracle for disposable revocation diagnostic readback.

A valid-looking row under a weakened table with identical SQLite object
names is not sufficient durable-veto evidence. No user DB, scope or retry.
"""

import sqlite3
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_ddl_run895", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


def _foreign_schema(path: Path, ddl: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(ddl)
        conn.execute("PRAGMA user_version=1")
        conn.execute(
            "INSERT INTO synthetic_context_revocations VALUES (?, ?)",
            (_DIAG._SCOPE_DIGEST, 2000),
        )


@pytest.mark.parametrize(
    "ddl",
    (
        "CREATE TABLE synthetic_context_revocations("
        "scope_digest TEXT PRIMARY KEY, revoked_at_ms INTEGER)",
        "CREATE TABLE synthetic_context_revocations("
        "scope_digest TEXT PRIMARY KEY NOT NULL, revoked_at_ms INTEGER)",
        "CREATE TABLE synthetic_context_revocations("
        "scope_digest TEXT PRIMARY KEY NOT NULL, revoked_at_ms INTEGER NOT NULL "
        "CHECK(revoked_at_ms >= 0))",
    ),
    ids=("both-not-null-missing", "timestamp-not-null-missing", "extra-check"),
)
def test_matching_row_and_autoindex_cannot_hide_schema_downgrade(tmp_path, ddl):
    path = tmp_path / "altered-v1.sqlite"
    _foreign_schema(path, ddl)
    with sqlite3.connect(path) as conn:
        objects = conn.execute(
            "SELECT type,name,tbl_name FROM sqlite_master ORDER BY type,name"
        ).fetchall()
    # Under the old type/name-only oracle this fixture was falsely accepted.
    assert objects == [
        ("index", "sqlite_autoindex_synthetic_context_revocations_1",
         "synthetic_context_revocations"),
        ("table", "synthetic_context_revocations",
         "synthetic_context_revocations"),
    ]
    assert _DIAG._verify_row(path) is False


def test_canonical_schema_and_one_synthetic_veto_still_verify(tmp_path):
    from ark.memory import MemoryScope
    from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

    path = tmp_path / "canonical-v1.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    ledger.revoke(MemoryScope("synthetic-diagnostic", "profile"), at_ms=2000)
    assert _DIAG._verify_row(path) is True
