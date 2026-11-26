"""Disposable action audit receipts require the original SQLite schema.

Synthetic readback is not independent evidence of real external action.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts" / "diagnose_audit_sidecar_startup.py"
)


def _load():
    spec = util.spec_from_file_location("audit_schema_custody_run833", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_DIAG = _load()


@pytest.mark.parametrize(
    "mutation",
    (
        "PRAGMA user_version=2",
        "CREATE INDEX untrusted_extra_index ON action_events(outcome)",
        "CREATE TRIGGER untrusted_extra_trigger AFTER INSERT ON action_events "
        "BEGIN SELECT 1; END",
    ),
)
def test_readback_refuses_schema_drift_despite_matching_synthetic_rows(
    tmp_path: Path, mutation: str,
) -> None:
    path = tmp_path / "audit.sqlite"
    assert _DIAG._probe(path, "sequential", wal_keeper=True) == [
        {"status": "AUDITED"}, {"status": "AUDITED"},
    ]
    assert _DIAG._verify_disposable_audit(path)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(mutation)
        conn.commit()
    assert _DIAG._verify_disposable_audit(path) is False


def test_readback_blob_identity_fails_closed_without_sort_typeerror(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite"
    assert _DIAG._probe(path, "sequential", wal_keeper=True) == [
        {"status": "AUDITED"}, {"status": "AUDITED"},
    ]
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "UPDATE action_events SET request_id=? WHERE event_id=2",
            (sqlite3.Binary(bytes((255, 0))),),
        )
        conn.commit()
    assert _DIAG._verify_disposable_audit(path) is False
