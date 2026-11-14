"""ActionAudit v1 SQLite main/sidecar alias checks on synthetic temp files."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit, _require_safe_audit_path
from ark.agency.contracts import ActionAuditSchemaError


def _sidecar(path: Path, suffix: str) -> Path:
    return path.with_name(path.name + suffix)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_orphan_journal_denied_before_audit_db_bootstrap(tmp_path, suffix):
    path = tmp_path / "audit.sqlite"
    journal = _sidecar(path, suffix)
    journal.write_bytes(b"unverified old synthetic journal")
    with pytest.raises(ActionAuditSchemaError, match="orphaned"):
        SQLiteActionAudit(path)
    assert not path.exists()
    assert journal.read_bytes() == b"unverified old synthetic journal"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_symlink_sidecar_denied_on_existing_audit_db(tmp_path, suffix):
    path = tmp_path / "audit.sqlite"
    SQLiteActionAudit(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained journal; do not disturb it")
    source = tmp_path / "other"
    source.write_bytes(b"synthetic protected bytes")
    try:
        alias.symlink_to(source)
    except (OSError, NotImplementedError):
        pytest.skip("runner cannot create symlinks")
    with pytest.raises(ActionAuditSchemaError, match="sidecar"):
        _require_safe_audit_path(path, allow_new_parents=False)
    assert source.read_bytes() == b"synthetic protected bytes"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_hardlink_sidecar_denied_on_existing_audit_db(tmp_path, suffix):
    path = tmp_path / "audit.sqlite"
    SQLiteActionAudit(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained journal; do not disturb it")
    source = tmp_path / "other"
    source.write_bytes(b"synthetic protected bytes")
    os.link(source, alias)
    with pytest.raises(ActionAuditSchemaError, match="sidecar"):
        _require_safe_audit_path(path, allow_new_parents=False)
    assert source.read_bytes() == b"synthetic protected bytes"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_directory_sidecar_denied_on_existing_audit_db(tmp_path, suffix):
    path = tmp_path / "audit.sqlite"
    SQLiteActionAudit(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained journal; do not disturb it")
    alias.mkdir()
    with pytest.raises(ActionAuditSchemaError, match="sidecar"):
        _require_safe_audit_path(path, allow_new_parents=False)
    assert alias.is_dir()


@pytest.mark.skipif(os.name != "posix", reason="FIFO requires POSIX")
def test_fifo_sidecar_denied_on_existing_audit_db(tmp_path):
    path = tmp_path / "audit.sqlite"
    SQLiteActionAudit(path)
    alias = _sidecar(path, "-journal")
    if alias.exists():
        pytest.skip("SQLite retained journal; do not disturb it")
    os.mkfifo(alias)
    with pytest.raises(ActionAuditSchemaError, match="sidecar"):
        _require_safe_audit_path(path, allow_new_parents=False)


def test_valid_regular_sidecars_preserve_local_audit_path_check(tmp_path):
    path = tmp_path / "audit.sqlite"
    SQLiteActionAudit(path)
    for suffix in ("-wal", "-shm", "-journal"):
        alias = _sidecar(path, suffix)
        if not alias.exists():
            alias.write_bytes(b"regular synthetic journal metadata")
    _require_safe_audit_path(path, allow_new_parents=False)
