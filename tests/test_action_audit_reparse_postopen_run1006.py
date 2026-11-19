"""Synthetic reparse-point and post-open custody regressions for Action Audit."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.audit as audit_module
from ark.agency.audit import ActionAuditSchemaError, SQLiteActionAudit


def _audit(tmp_path: Path) -> SQLiteActionAudit:
    return SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 100)


def _mark_reparse_point(monkeypatch, target: Path) -> None:
    original_lstat = Path.lstat

    def marked_lstat(path):
        info = original_lstat(path)
        if path == target:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_nlink=info.st_nlink,
                st_file_attributes=0x400,
            )
        return info

    monkeypatch.setattr(Path, "lstat", marked_lstat)


def _reparse_after_open(monkeypatch, target: Path):
    original_lstat = Path.lstat
    state = {"opened": False}

    def marked_lstat(path):
        info = original_lstat(path)
        if state["opened"] and path == target:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_nlink=info.st_nlink,
                st_file_attributes=0x400,
            )
        return info

    monkeypatch.setattr(Path, "lstat", marked_lstat)
    original_connect = audit_module.sqlite3.connect
    opened = []

    def connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        state["opened"] = True
        return connection

    monkeypatch.setattr(audit_module.sqlite3, "connect", connect)
    return opened


def _assert_closed(connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


@pytest.mark.parametrize("location", ["ancestor", "main", "sidecar"])
def test_audit_rejects_reparse_point_before_sqlite_open(
    tmp_path: Path, monkeypatch, location: str,
) -> None:
    audit = _audit(tmp_path)
    if location == "ancestor":
        target = tmp_path
    elif location == "main":
        target = audit.path
    else:
        target = audit.path.with_name(audit.path.name + "-wal")
        target.write_bytes(b"synthetic sidecar")

    _mark_reparse_point(monkeypatch, target)

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("reparse-point audit path reached SQLite")

    monkeypatch.setattr(audit_module.sqlite3, "connect", forbidden_connect)
    with pytest.raises(ActionAuditSchemaError, match="reparse|sidecar alias"):
        audit._connect()


def test_audit_reparse_attribute_requires_exact_integer() -> None:
    assert audit_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=0x400)
    )
    assert not audit_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=0)
    )
    assert audit_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=True)
    )


@pytest.mark.parametrize("method", ["_connect", "_connect_readonly"])
def test_audit_rechecks_path_after_open_and_closes_rejected_handle(
    tmp_path: Path, monkeypatch, method: str,
) -> None:
    audit = _audit(tmp_path)
    opened = _reparse_after_open(monkeypatch, audit.path)

    with pytest.raises(
        ActionAuditSchemaError,
        match="regular non-reparse file link",
    ):
        getattr(audit, method)()

    assert len(opened) == 1
    _assert_closed(opened[0])


def test_audit_constructor_rechecks_path_after_bootstrap_open_and_closes_handle(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "new-audit.sqlite"
    opened = _reparse_after_open(monkeypatch, path)

    with pytest.raises(
        ActionAuditSchemaError,
        match="regular non-reparse file link",
    ):
        SQLiteActionAudit(path, clock_ms=lambda: 100)

    assert len(opened) == 1
    _assert_closed(opened[0])
