"""ActionAudit rejects Windows reparse-point paths before SQLite access.

The tests simulate st_file_attributes so they run without creating privileged
Windows junctions. No external action or authenticated audit claim is involved.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _reparse_info(mode: int):
    return SimpleNamespace(
        st_mode=mode,
        st_file_attributes=0x400,
        st_nlink=1,
    )


def test_reparse_point_ancestor_is_rejected_before_parent_creation(tmp_path, monkeypatch):
    parent = tmp_path / "junction"
    parent.mkdir()
    missing = parent / "new"
    path = missing / "audit.sqlite"
    original_lstat = Path.lstat

    def lstat(candidate):
        if candidate == parent:
            return _reparse_info(stat.S_IFDIR | 0o755)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ActionAuditSchemaError, match="reparse-point ancestor"):
        SQLiteActionAudit(path)

    assert not missing.exists()
    assert not path.exists()


def test_reparse_point_database_leaf_is_rejected_before_sqlite_open(tmp_path, monkeypatch):
    path = tmp_path / "audit.sqlite"
    original_lstat = Path.lstat

    def lstat(candidate):
        if candidate == path:
            return _reparse_info(stat.S_IFREG | 0o600)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ActionAuditSchemaError, match="reparse-point path"):
        SQLiteActionAudit(path)

    assert not path.exists()


def test_reparse_point_sqlite_sidecar_is_rejected_before_reopen(tmp_path, monkeypatch):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 100)
    audit.append(
        ToolCall("fixture.audit", "mock.read", "synthetic", {"n": 1}),
        outcome="synthetic-only",
    )
    sidecar = path.with_name(path.name + "-wal")
    sidecar.write_bytes(b"synthetic sidecar marker")
    original_lstat = Path.lstat

    def lstat(candidate):
        if candidate == sidecar:
            return _reparse_info(stat.S_IFREG | 0o600)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ActionAuditSchemaError, match="sidecar reparse-point"):
        SQLiteActionAudit(path, clock_ms=lambda: 101)

    assert path.exists()


def test_reparse_point_policy_cannot_be_rebound_before_path_inspection(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(audit_module, "_REPARSE_POINT_ATTRIBUTE", 0x800)
    with pytest.raises(ActionAuditSchemaError, match="reparse-point policy changed"):
        audit_module._require_safe_audit_path(
            tmp_path / "audit.sqlite",
            allow_new_parents=True,
        )
