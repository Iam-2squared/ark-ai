"""Detached action audit readback remains coherent across a WAL writer.

No real tool or network operation runs. These are disposable SQLite fixtures,
not a trusted clock, an action approval, or external-effect evidence.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from importlib import util
from pathlib import Path

import pytest

import ark.agency.audit as audit_module

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_audit_sidecar_startup.py"
_SPEC = util.spec_from_file_location("audit_diag_coherent_run835", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


@pytest.mark.parametrize(("column", "replacement"), (
    ("outcome", "foreign_outcome"),
    ("occurred_at_ms", 987654),
))
def test_wal_writer_between_schema_check_and_receipt_read_stays_one_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    column: str, replacement: object,
) -> None:
    path = tmp_path / "audit.sqlite"
    assert _DIAG._probe(path, "sequential", wal_keeper=True) == [
        {"status": "AUDITED"}, {"status": "AUDITED"},
    ]
    assert _DIAG._verify_disposable_audit(path)
    original = audit_module._validate_v1_schema
    interleaved = False

    def write_after_schema(conn: sqlite3.Connection) -> None:
        nonlocal interleaved
        assert conn.in_transaction
        original(conn)
        with closing(sqlite3.connect(path)) as writer:
            writer.execute(
                f"UPDATE action_events SET {column}=? WHERE event_id=1",
                (replacement,),
            )
            writer.commit()
        interleaved = True

    with monkeypatch.context() as patch:
        patch.setattr(audit_module, "_validate_v1_schema", write_after_schema)
        assert _DIAG._verify_disposable_audit(path)
    assert interleaved
    assert not _DIAG._verify_disposable_audit(path)


def test_unexpected_trigger_cannot_inherit_prior_clean_child_receipts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite"
    assert _DIAG._probe(path, "sequential", wal_keeper=True) == [
        {"status": "AUDITED"}, {"status": "AUDITED"},
    ]
    assert _DIAG._verify_disposable_audit(path)
    with closing(sqlite3.connect(path)) as writer:
        writer.execute(
            "CREATE TRIGGER extra BEFORE UPDATE ON action_events "
            "BEGIN SELECT 1; END"
        )
        writer.commit()
    assert not _DIAG._verify_disposable_audit(path)
