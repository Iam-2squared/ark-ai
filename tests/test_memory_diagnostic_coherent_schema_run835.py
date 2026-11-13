"""Frozen Memory DDL and fixture rows must share one read-only WAL epoch.

All data are disposable; neither a synthetic child receipt nor a matched row
authenticates a historical writer, a retry decision, or an external action.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

import ark.memory.sqlite_store as memory_sqlite

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_memory_sidecar_startup.py"
_SPEC = util.spec_from_file_location("memory_diag_coherent_run835", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


@pytest.mark.parametrize("ddl", (
    "PRAGMA user_version=2",
    "DROP INDEX idx_mem_expiry",
    "CREATE VIEW diagnostic_extra AS SELECT 1",
    "CREATE TRIGGER diagnostic_extra BEFORE UPDATE ON memories "
    "BEGIN SELECT 1; END",
))
def test_persisted_fixture_rows_do_not_override_frozen_schema(
    tmp_path: Path, ddl: str,
) -> None:
    path = tmp_path / "memory.sqlite"
    results = _DIAG._probe(
        path, "separate-owner", "sequential", wal_keeper=True,
    )
    assert [item["status"] for item in results] == ["CREATED", "CREATED"]
    assert _DIAG._verify_disposable_commit(path, "separate-owner", "create")
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(ddl)
        conn.commit()
    assert not _DIAG._verify_disposable_commit(path, "separate-owner", "create")


def test_concurrent_wal_write_does_not_mix_schema_and_row_epochs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "memory.sqlite"
    assert all(
        item["status"] == "CREATED"
        for item in _DIAG._probe(
            path, "separate-owner", "sequential", wal_keeper=True,
        )
    )
    assert _DIAG._verify_disposable_commit(path, "separate-owner", "create")
    original = memory_sqlite._validate_v1_schema
    interleaved = False

    def commit_between_checks(conn: sqlite3.Connection) -> None:
        nonlocal interleaved
        assert conn.in_transaction
        original(conn)
        with closing(sqlite3.connect(path)) as writer:
            writer.execute(
                "UPDATE memories SET content='foreign' WHERE owner_id='owner-a'"
            )
            writer.commit()
        interleaved = True

    with monkeypatch.context() as patch:
        patch.setattr(
            memory_sqlite, "_validate_v1_schema", commit_between_checks,
        )
        # The read transaction began before the simulated foreign writer.
        assert _DIAG._verify_disposable_commit(path, "separate-owner", "create")
    assert interleaved
    # A subsequent independent read sees the committed foreign value and
    # correctly refuses the synthetic expected-row claim.
    assert not _DIAG._verify_disposable_commit(path, "separate-owner", "create")
