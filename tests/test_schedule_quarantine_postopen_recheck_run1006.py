"""Post-open path rechecks for the disconnected schedule quarantine ledger."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.disconnected_schedule_quarantine_ledger as ledger_module
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
)


def _policy() -> QuarantinePolicy:
    return QuarantinePolicy(
        policy_sha256="a" * 64,
        first_ms=10_000,
        interval_ms=5_000,
        count=3,
        grace_ms=500,
    )


def _fresh(tmp_path: Path):
    policy = _policy()
    path = tmp_path / "quarantine.db"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    return ledger, policy, path


def _reparse_after_open(monkeypatch, target: Path):
    """Change only the post-connect lstat view; keep the SQLite handle real."""
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
    original_connect = ledger_module.sqlite3.connect
    opened = []

    def connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        state["opened"] = True
        return connection

    monkeypatch.setattr(ledger_module.sqlite3, "connect", connect)
    return opened


def _assert_closed(connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


@pytest.mark.parametrize("read_only", [False, True])
def test_quarantine_rechecks_path_after_read_or_write_open_and_closes_handle(
    tmp_path: Path, monkeypatch, read_only: bool,
) -> None:
    ledger, _policy_value, path = _fresh(tmp_path)
    opened = _reparse_after_open(monkeypatch, path)

    with pytest.raises(
        ScheduleQuarantineRejected,
        match="aliased or existing quarantine ledger",
    ):
        ledger._open(read_only=read_only)

    assert len(opened) == 1
    _assert_closed(opened[0])


@pytest.mark.parametrize("create", [False, True])
def test_quarantine_constructor_rechecks_path_after_startup_open_and_closes_handle(
    tmp_path: Path, monkeypatch, create: bool,
) -> None:
    policy = _policy()
    if create:
        parent = tmp_path / "new"
        parent.mkdir()
        path = parent / "quarantine.db"
    else:
        _ledger, _policy_value, path = _fresh(tmp_path)

    opened = _reparse_after_open(monkeypatch, path)
    with pytest.raises(
        ScheduleQuarantineRejected,
        match="aliased or existing quarantine ledger",
    ):
        DisconnectedScheduleQuarantineLedger(
            path, policy=policy, create=create,
        )

    assert len(opened) == 1
    _assert_closed(opened[0])
