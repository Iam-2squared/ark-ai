"""Disposable Memory/ActionAudit path-only WAL unlink preflight regression.

No user database is opened. A synthetic pathname regular-inode recheck must
not permit symlinks, hardlinks, stale unlinked inodes or orphan sidecars.
"""

from __future__ import annotations

import stat
from types import SimpleNamespace

import pytest

from ark.agency.audit import _require_safe_audit_path
from ark.agency.contracts import ActionAuditSchemaError
from ark.memory import MemorySchemaError
from ark.memory.sqlite_store import _require_safe_memory_path


def _preflight(kind, path):
    if kind == "memory":
        return _require_safe_memory_path(path, create=False)
    return _require_safe_audit_path(path, allow_new_parents=False)


def _assert_rejected(kind, path):
    rejection = MemorySchemaError if kind == "memory" else ActionAuditSchemaError
    with pytest.raises(rejection, match="sidecar"):
        _preflight(kind, path)


def _fake_unlinked_first(monkeypatch, sidecar):
    kind = type(sidecar)
    original = kind.lstat
    calls: list[int] = []

    def lstat(self, *args, **kwargs):
        if self == sidecar:
            calls.append(1)
            if len(calls) == 1:
                return SimpleNamespace(
                    st_mode=stat.S_IFREG | 0o600, st_nlink=0,
                )
        return original(self, *args, **kwargs)

    monkeypatch.setattr(kind, "lstat", lstat)
    return calls


@pytest.mark.parametrize("kind", ("memory", "audit"))
@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_dangling_unlinked_regular_sidecar_is_rechecked_once(
    tmp_path, monkeypatch, kind, suffix,
):
    path = tmp_path / f"{kind}-synthetic.sqlite"
    path.write_bytes(b"path-only stub: do not open as SQLite")
    sidecar = path.with_name(path.name + suffix)
    assert not sidecar.exists()
    calls = _fake_unlinked_first(monkeypatch, sidecar)
    _preflight(kind, path)
    assert len(calls) == 2


@pytest.mark.parametrize("kind", ("memory", "audit"))
@pytest.mark.parametrize("substitute", ("regular", "hardlink", "symlink"))
def test_stale_regular_inode_requires_safe_fresh_sidecar(
    tmp_path, monkeypatch, kind, substitute,
):
    path = tmp_path / f"{kind}-synthetic.sqlite"
    path.write_bytes(b"path-only stub")
    sidecar = path.with_name(path.name + "-shm")
    if substitute == "regular":
        sidecar.write_bytes(b"new local single-link inode")
    else:
        private_target = tmp_path / "untouched-private-marker"
        private_target.write_bytes(b"target must remain unchanged")
        try:
            if substitute == "hardlink":
                sidecar.hardlink_to(private_target)
            else:
                sidecar.symlink_to(private_target)
        except OSError as exc:
            pytest.skip(f"filesystem cannot create {substitute}: {exc}")
    calls = _fake_unlinked_first(monkeypatch, sidecar)
    if substitute == "regular":
        _preflight(kind, path)
    else:
        _assert_rejected(kind, path)
        assert private_target.read_bytes() == b"target must remain unchanged"
    assert len(calls) == 2


@pytest.mark.parametrize("kind", ("memory", "audit"))
def test_still_unlinked_inode_is_denied_after_one_recheck(
    tmp_path, monkeypatch, kind,
):
    path = tmp_path / f"{kind}-synthetic.sqlite"
    path.write_bytes(b"path-only stub")
    sidecar = path.with_name(path.name + "-wal")
    original = type(sidecar).lstat
    calls: list[int] = []

    def lstat(self, *args, **kwargs):
        if self == sidecar:
            calls.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", lstat)
    _assert_rejected(kind, path)
    assert len(calls) == 2


@pytest.mark.parametrize("kind", ("memory", "audit"))
def test_uninitialized_database_never_adopts_orphan_sidecar(
    tmp_path, monkeypatch, kind,
):
    path = tmp_path / f"missing-{kind}.sqlite"
    sidecar = path.with_name(path.name + "-journal")
    sidecar.write_bytes(b"orphaned fixture")
    calls = _fake_unlinked_first(monkeypatch, sidecar)
    # Only check the path preflight; creating the real database is forbidden.
    if kind == "memory":
        with pytest.raises(MemorySchemaError, match="orphaned.*sidecar"):
            _require_safe_memory_path(path, create=True)
    else:
        with pytest.raises(ActionAuditSchemaError, match="orphaned.*sidecar"):
            _require_safe_audit_path(path, allow_new_parents=True)
    assert len(calls) == 1
    assert not path.exists()
    assert sidecar.read_bytes() == b"orphaned fixture"
