"""WRITE Slot Ledger pathname safety during SQLite final-sidecar unlink.

These tests use stub files and injected filesystem metadata only, never open
a real ledger or grant permission to dispatch an external WRITE operation.
"""

from __future__ import annotations

import stat
from types import SimpleNamespace

import pytest

from ark.agency.disconnected_write_slot_ledger import (
    WriteSlotLedgerRejected,
    _check_path,
)


def _simulate_old_unlinked(monkeypatch, sidecar, *, mode=stat.S_IFREG):
    original = type(sidecar).lstat
    seen = []

    def observe(self, *args, **kwargs):
        if self == sidecar:
            seen.append(1)
            if len(seen) == 1:
                return SimpleNamespace(st_mode=mode | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", observe)
    return seen


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_regular_last_close_unlink_reobserved_once(
    tmp_path, monkeypatch, suffix,
):
    db = tmp_path / "write-slot.sqlite"
    db.write_bytes(b"no SQLite content")
    sidecar = db.with_name(db.name + suffix)
    seen = _simulate_old_unlinked(monkeypatch, sidecar)
    assert _check_path(db, create=False) is db
    assert seen == [1, 1]


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("replacement", ("regular", "hardlink", "symlink"))
def test_recheck_does_not_admit_alias_and_never_changes_target(
    tmp_path, monkeypatch, suffix, replacement,
):
    db = tmp_path / "write-slot.sqlite"
    db.write_bytes(b"path-only fixture")
    sidecar = db.with_name(db.name + suffix)
    if replacement == "regular":
        sidecar.write_bytes(b"safe replacement")
    else:
        target = tmp_path / "private-target"
        target.write_bytes(b"unchanged marker")
        try:
            if replacement == "hardlink":
                sidecar.hardlink_to(target)
            else:
                sidecar.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"filesystem cannot create {replacement}: {exc}")
    seen = _simulate_old_unlinked(monkeypatch, sidecar)
    if replacement == "regular":
        assert _check_path(db, create=False) is db
    else:
        with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
            _check_path(db, create=False)
        assert target.read_bytes() == b"unchanged marker"
    assert seen == [1, 1]


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_still_unlinked_regular_inode_is_denied_after_second_look(
    tmp_path, monkeypatch, suffix,
):
    db = tmp_path / "write-slot.sqlite"
    db.write_bytes(b"path-only fixture")
    sidecar = db.with_name(db.name + suffix)
    original = type(sidecar).lstat
    seen = []

    def observe(self, *args, **kwargs):
        if self == sidecar:
            seen.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", observe)
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        _check_path(db, create=False)
    assert seen == [1, 1]


@pytest.mark.parametrize("mode", (stat.S_IFLNK, stat.S_IFDIR))
def test_special_zero_link_inode_does_not_get_a_retry(
    tmp_path, monkeypatch, mode,
):
    db = tmp_path / "write-slot.sqlite"
    db.write_bytes(b"path-only fixture")
    sidecar = db.with_name(db.name + "-shm")
    seen = _simulate_old_unlinked(monkeypatch, sidecar, mode=mode)
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        _check_path(db, create=False)
    assert seen == [1]


def test_first_creation_never_adopts_orphan_sidecar(
    tmp_path, monkeypatch,
):
    db = tmp_path / "missing-write-slot.sqlite"
    sidecar = db.with_name(db.name + "-journal")
    seen = _simulate_old_unlinked(monkeypatch, sidecar)
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        _check_path(db, create=True)
    assert seen == [1]
    assert not db.exists()
