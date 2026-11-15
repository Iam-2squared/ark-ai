"""Disposable revocation readback cannot certify aliases of the SQLite file.

These fixtures contain only a synthetic scope. They do not demonstrate atomic
open-handle ownership, authenticated provenance, consent or WRITE authority.
"""

import os
import sqlite3
from importlib import util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_revocation_wal_processes.py"
_SPEC = util.spec_from_file_location("revocation_wal_alias_run896", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_DIAG = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_DIAG)


def _valid_synthetic_veto(path: Path) -> None:
    from ark.memory import MemoryScope
    from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

    ledger = SyntheticContextRevocationLedger(path)
    ledger.revoke(MemoryScope("synthetic-diagnostic", "profile"), at_ms=2000)


def test_hardlink_alias_cannot_certify_durable_veto(tmp_path):
    path = tmp_path / "canonical.sqlite"
    _valid_synthetic_veto(path)
    assert _DIAG._verify_row(path) is True
    alias = tmp_path / "alias.sqlite"
    try:
        os.link(path, alias)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem cannot create hardlinks: {exc}")
    try:
        assert _DIAG._verify_row(alias) is False
        assert _DIAG._verify_row(path) is False
    finally:
        alias.unlink()
    assert _DIAG._verify_row(path) is True


def test_symlink_alias_cannot_certify_durable_veto(tmp_path):
    path = tmp_path / "canonical.sqlite"
    _valid_synthetic_veto(path)
    alias = tmp_path / "alias.sqlite"
    try:
        alias.symlink_to(path)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem cannot create symlinks: {exc}")
    assert _DIAG._verify_row(alias) is False
    assert _DIAG._verify_row(path) is True


@pytest.mark.parametrize("kind", ("directory", "absent", "foreign-db"))
def test_noncanonical_veto_path_is_denied(tmp_path, kind):
    path = tmp_path / "not-veto.sqlite"
    if kind == "directory":
        path.mkdir()
    elif kind == "foreign-db":
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE unrelated(value TEXT)")
    assert _DIAG._verify_row(path) is False
