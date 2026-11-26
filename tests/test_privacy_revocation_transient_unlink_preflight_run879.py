"""One bounded re-lstat for unlinking SQLite veto sidecars; never alias trust.

The fixture fabricates inode metadata only on a disposable local path. It
does not authorize consent, restore data, or open a real user database.
"""

from __future__ import annotations

import stat
from types import SimpleNamespace

import pytest

from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    _check_local_revocation_path,
)


def _fake_unlinked_first(monkeypatch, sidecar):
    path_type = type(sidecar)
    original = path_type.lstat
    observed: list[int] = []

    def guarded_lstat(self, *args, **kwargs):
        if self == sidecar:
            observed.append(1)
            if len(observed) == 1:
                return SimpleNamespace(
                    st_mode=stat.S_IFREG | 0o600, st_nlink=0,
                )
        return original(self, *args, **kwargs)

    monkeypatch.setattr(path_type, "lstat", guarded_lstat)
    return observed


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_unlinked_regular_sidecar_that_vanishes_is_rechecked_once(
    tmp_path, monkeypatch, suffix,
):
    db = tmp_path / "veto.sqlite"
    SyntheticContextRevocationLedger(db)
    sidecar = db.with_name(db.name + suffix)
    assert not sidecar.exists()
    observed = _fake_unlinked_first(monkeypatch, sidecar)
    _check_local_revocation_path(db)
    assert len(observed) == 2


@pytest.mark.parametrize("kind", ("regular", "hardlink", "symlink"))
def test_unlinked_snapshot_requires_fresh_safe_path_before_acceptance(
    tmp_path, monkeypatch, kind,
):
    db = tmp_path / "veto.sqlite"
    SyntheticContextRevocationLedger(db)
    sidecar = db.with_name(db.name + "-journal")
    if kind == "regular":
        sidecar.write_bytes(b"disposable-journal-marker")
    else:
        private_target = tmp_path / "unrelated-data"
        private_target.write_bytes(b"not a journal")
        try:
            if kind == "hardlink":
                sidecar.hardlink_to(private_target)
            else:
                sidecar.symlink_to(private_target)
        except OSError as exc:
            pytest.skip(f"filesystem does not support {kind}: {exc}")
    observed = _fake_unlinked_first(monkeypatch, sidecar)
    if kind == "regular":
        _check_local_revocation_path(db)
    else:
        with pytest.raises(
            SyntheticContextRevocationRejected, match="unsafe.*sidecar",
        ):
            _check_local_revocation_path(db)
        assert private_target.read_bytes() == b"not a journal"
    assert len(observed) == 2


def test_still_unlinked_inode_is_refused_even_after_retry(
    tmp_path, monkeypatch,
):
    db = tmp_path / "veto.sqlite"
    SyntheticContextRevocationLedger(db)
    sidecar = db.with_name(db.name + "-journal")
    original = type(sidecar).lstat
    observed: list[int] = []

    def permanently_unlinked(self, *args, **kwargs):
        if self == sidecar:
            observed.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", permanently_unlinked)
    with pytest.raises(SyntheticContextRevocationRejected, match="sidecar"):
        _check_local_revocation_path(db)
    assert len(observed) == 2


def test_orphan_regular_sidecar_still_fails_without_retry(tmp_path, monkeypatch):
    db = tmp_path / "missing.sqlite"
    sidecar = db.with_name(db.name + "-journal")
    sidecar.write_bytes(b"untrusted orphan")
    observed = _fake_unlinked_first(monkeypatch, sidecar)
    with pytest.raises(SyntheticContextRevocationRejected, match="sidecar"):
        _check_local_revocation_path(db)
    assert len(observed) == 1
    assert not db.exists()
    assert sidecar.read_bytes() == b"untrusted orphan"
