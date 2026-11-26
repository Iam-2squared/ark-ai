"""Disposable WAL diagnostic: bounded verification of a single synthetic veto.

No personal scope, real database, authorization, external tool or retry is used.
"""

import sqlite3
from importlib import util
from pathlib import Path

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_bounded_readback_run894", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


def _fixture(tmp_path):
    path = tmp_path / "synthetic-veto.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    ledger.revoke(MemoryScope("synthetic-diagnostic", "profile"), at_ms=2000)
    return path, ledger


def test_exact_one_row_disposable_veto_is_verified(tmp_path):
    path, _ledger = _fixture(tmp_path)
    assert _DIAG._verify_row(path) is True


def test_second_veto_row_is_not_mistaken_for_exact_durable_witness(tmp_path):
    path, ledger = _fixture(tmp_path)
    ledger.revoke(MemoryScope("synthetic-diagnostic", "other"), at_ms=2000)
    assert _DIAG._verify_row(path) is False


def test_unexpected_catalog_object_is_not_mistaken_for_frozen_fixture(tmp_path):
    path, _ledger = _fixture(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE synthetic_extra_object(value INTEGER)")
    assert _DIAG._verify_row(path) is False
