"""Disposable Memory receipts must bind every persisted row and event field.

A synthetically successful subprocess is never independent durable authority.
No real user memory, external action, or trusted clock is involved.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "diagnose_memory_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("memory_full_receipt_run833", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("metadata_json", '{"substituted":"yes"}'),
        ("content_sha256", "0" * 64),
        ("created_at_ms", 1001),
        ("updated_at_ms", 1001),
        ("expires_at_ms", 1),
    ),
)
def test_memory_receipt_refuses_incorrect_row_evidence(
    tmp_path: Path, column: str, value: object,
) -> None:
    path = tmp_path / "memory.sqlite"
    assert [item["status"] for item in _DIAG._probe(
        path, "separate-owner", "sequential", wal_keeper=True,
    )] == ["CREATED", "CREATED"]
    assert _DIAG._verify_disposable_commit(path, "separate-owner", "create")
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE owner_id='owner-b'",
            (value,),
        )
        conn.commit()
    assert not _DIAG._verify_disposable_commit(path, "separate-owner", "create")


def test_memory_receipt_refuses_incorrect_event_time(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite"
    assert all(item["status"] == "UPDATED" for item in _DIAG._probe(
        path, "separate-owner", "sequential", "generation-cas",
        wal_keeper=True,
    ))
    assert _DIAG._verify_disposable_commit(path, "separate-owner", "generation-cas")
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("UPDATE memory_events SET occurred_at_ms=1001 WHERE event_id=2")
        conn.commit()
    assert not _DIAG._verify_disposable_commit(
        path, "separate-owner", "generation-cas",
    )


def test_memory_receipt_blob_identity_is_false_not_traceback(tmp_path: Path) -> None:
    path = tmp_path / "memory.sqlite"
    assert all(item["status"] == "CREATED" for item in _DIAG._probe(
        path, "separate-owner", "sequential", wal_keeper=True,
    ))
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "UPDATE memories SET memory_id=? WHERE owner_id='owner-b'",
            (sqlite3.Binary(b"\\xff"),),
        )
        conn.commit()
    assert _DIAG._verify_disposable_commit(path, "separate-owner", "create") is False
