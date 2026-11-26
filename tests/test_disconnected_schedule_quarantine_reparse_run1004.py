"""Synthetic Windows reparse-point admission for the schedule quarantine ledger."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    genesis_quarantine_witness,
)


def _fresh(tmp_path: Path):
    policy = QuarantinePolicy(
        policy_sha256="a" * 64,
        first_ms=10_000,
        interval_ms=5_000,
        count=3,
        grace_ms=500,
    )
    path = tmp_path / "quarantine.db"
    ledger = DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    return ledger, policy, path


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


def test_quarantine_rejects_reparse_point_ancestor_before_sqlite_open(
    tmp_path, monkeypatch,
):
    ledger, policy, _ = _fresh(tmp_path)
    _mark_reparse_point(monkeypatch, tmp_path)

    with pytest.raises(ScheduleQuarantineRejected, match="unsafe quarantine ancestor"):
        ledger.inspect(retained=genesis_quarantine_witness(policy))


def test_quarantine_rejects_reparse_point_main_database(tmp_path, monkeypatch):
    ledger, policy, path = _fresh(tmp_path)
    _mark_reparse_point(monkeypatch, path)

    with pytest.raises(
        ScheduleQuarantineRejected,
        match="aliased or existing quarantine ledger",
    ):
        ledger.inspect(retained=genesis_quarantine_witness(policy))


def test_quarantine_rejects_reparse_point_sqlite_sidecar(tmp_path, monkeypatch):
    ledger, policy, path = _fresh(tmp_path)
    sidecar = path.with_name(path.name + "-wal")
    sidecar.write_bytes(b"synthetic sidecar marker")
    _mark_reparse_point(monkeypatch, sidecar)

    with pytest.raises(
        ScheduleQuarantineRejected,
        match="unsafe quarantine SQLite sidecar",
    ):
        ledger.inspect(retained=genesis_quarantine_witness(policy))
