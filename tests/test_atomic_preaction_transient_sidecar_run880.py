"""Disconnected atomic preaction ledger: conservative SQLite unlink race fence.

Only disposable filesystem preflight stubs; no tool, planner dispatch, token
issuer, trusted clock, irreversible action or cross-store transaction.
"""

from __future__ import annotations

import stat
from types import SimpleNamespace

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    _path,
)


def _unlinked_first(monkeypatch, sidecar, *, mode=stat.S_IFREG):
    original = type(sidecar).lstat
    seen = []

    def lstat(self, *args, **kwargs):
        if self == sidecar:
            seen.append(1)
            if len(seen) == 1:
                return SimpleNamespace(st_mode=mode | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", lstat)
    return seen


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_atomic_existing_ledger_tolerates_only_disappearing_regular_inode(
    tmp_path, monkeypatch, suffix,
):
    db = tmp_path / "atomic-intent.sqlite"
    db.write_bytes(b"not an active SQLite database")
    sidecar = db.with_name(db.name + suffix)
    seen = _unlinked_first(monkeypatch, sidecar)
    assert _path(db, create=False) == db
    assert seen == [1, 1]


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("replacement", ("regular", "hardlink", "symlink"))
def test_stale_metadata_never_grants_alias_admission(
    tmp_path, monkeypatch, suffix, replacement,
):
    db = tmp_path / "atomic-intent.sqlite"
    db.write_bytes(b"path-only fixture")
    sidecar = db.with_name(db.name + suffix)
    if replacement == "regular":
        sidecar.write_bytes(b"new single-link")
    else:
        target = tmp_path / "private-target"
        target.write_bytes(b"marker unchanged")
        try:
            if replacement == "hardlink":
                sidecar.hardlink_to(target)
            else:
                sidecar.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"filesystem cannot create {replacement}: {exc}")
    seen = _unlinked_first(monkeypatch, sidecar)
    if replacement == "regular":
        assert _path(db, create=False) == db
    else:
        with pytest.raises(AtomicPreactionRejected, match="sidecar"):
            _path(db, create=False)
        assert target.read_bytes() == b"marker unchanged"
    assert seen == [1, 1]


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_repeated_zero_link_is_not_retried_indefinitely(
    tmp_path, monkeypatch, suffix,
):
    db = tmp_path / "atomic-intent.sqlite"
    db.write_bytes(b"path-only fixture")
    sidecar = db.with_name(db.name + suffix)
    original = type(sidecar).lstat
    seen = []

    def lstat(self, *args, **kwargs):
        if self == sidecar:
            seen.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", lstat)
    with pytest.raises(AtomicPreactionRejected, match="sidecar"):
        _path(db, create=False)
    assert seen == [1, 1]


@pytest.mark.parametrize("mode", (stat.S_IFLNK, stat.S_IFDIR))
def test_special_inode_never_gets_second_observation(tmp_path, monkeypatch, mode):
    db = tmp_path / "atomic-intent.sqlite"
    db.write_bytes(b"path-only fixture")
    sidecar = db.with_name(db.name + "-wal")
    seen = _unlinked_first(monkeypatch, sidecar, mode=mode)
    with pytest.raises(AtomicPreactionRejected, match="sidecar"):
        _path(db, create=False)
    assert seen == [1]


def test_creation_still_refuses_any_orphan_sidecar_even_during_unlink(
    tmp_path, monkeypatch,
):
    db = tmp_path / "missing.sqlite"
    sidecar = db.with_name(db.name + "-journal")
    seen = _unlinked_first(monkeypatch, sidecar)
    with pytest.raises(AtomicPreactionRejected, match="sidecar"):
        _path(db, create=True)
    assert seen == [1]
    assert not db.exists()
