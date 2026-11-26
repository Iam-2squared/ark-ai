"""Synthetic occurrence ledger sidecar unlink-race admission regressions.

Disposable pathname metadata only. A successful preflight is never approval,
an execution receipt, provenance, consent or a reason to replay unknown writes.
"""

from __future__ import annotations

import stat
from types import SimpleNamespace

import pytest

from ark.agency.durable_occurrence_review import (
    SyntheticReplayRejected,
    _require_safe_occurrence_path,
)


def _observed_first_unlinked(monkeypatch, sidecar, *, mode=stat.S_IFREG):
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
def test_already_unlinked_regular_sidecar_may_disappear_on_one_recheck(
    tmp_path, monkeypatch, suffix,
):
    path = tmp_path / "occurrence.sqlite"
    path.write_bytes(b"path-only stub")
    sidecar = path.with_name(path.name + suffix)
    seen = _observed_first_unlinked(monkeypatch, sidecar)
    assert _require_safe_occurrence_path(path, create=False) is path
    assert seen == [1, 1]
    assert not sidecar.exists()


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("replacement", ("regular", "hardlink", "symlink"))
def test_recheck_requires_fresh_single_link_regular_inode(
    tmp_path, monkeypatch, suffix, replacement,
):
    path = tmp_path / "occurrence.sqlite"
    path.write_bytes(b"main stub")
    sidecar = path.with_name(path.name + suffix)
    if replacement == "regular":
        sidecar.write_bytes(b"safe local file")
    else:
        target = tmp_path / "unrelated-private-marker"
        target.write_bytes(b"must remain unchanged")
        try:
            if replacement == "hardlink":
                sidecar.hardlink_to(target)
            else:
                sidecar.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"filesystem does not support {replacement}: {exc}")
    seen = _observed_first_unlinked(monkeypatch, sidecar)
    if replacement == "regular":
        assert _require_safe_occurrence_path(path, create=False) is path
    else:
        with pytest.raises(SyntheticReplayRejected, match="sidecar alias"):
            _require_safe_occurrence_path(path, create=False)
        assert target.read_bytes() == b"must remain unchanged"
    assert seen == [1, 1]


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_continuously_unlinked_inode_is_denied_after_exactly_two_observations(
    tmp_path, monkeypatch, suffix,
):
    path = tmp_path / "occurrence.sqlite"
    path.write_bytes(b"main stub")
    sidecar = path.with_name(path.name + suffix)
    original = type(sidecar).lstat
    seen = []

    def lstat(self, *args, **kwargs):
        if self == sidecar:
            seen.append(1)
            return SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_nlink=0)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(type(sidecar), "lstat", lstat)
    with pytest.raises(SyntheticReplayRejected, match="sidecar alias"):
        _require_safe_occurrence_path(path, create=False)
    assert seen == [1, 1]


@pytest.mark.parametrize("mode", (stat.S_IFLNK, stat.S_IFDIR))
def test_special_file_not_rechecked_or_laundered(tmp_path, monkeypatch, mode):
    path = tmp_path / "occurrence.sqlite"
    path.write_bytes(b"main stub")
    sidecar = path.with_name(path.name + "-wal")
    seen = _observed_first_unlinked(monkeypatch, sidecar, mode=mode)
    with pytest.raises(SyntheticReplayRejected, match="sidecar alias"):
        _require_safe_occurrence_path(path, create=False)
    assert seen == [1]


def test_absent_main_with_sidecar_refuses_even_transient_unlink(
    tmp_path, monkeypatch,
):
    path = tmp_path / "never-create.sqlite"
    sidecar = path.with_name(path.name + "-journal")
    seen = _observed_first_unlinked(monkeypatch, sidecar)
    with pytest.raises(SyntheticReplayRejected, match="orphaned"):
        _require_safe_occurrence_path(path, create=True)
    assert seen == [1]
    assert not path.exists()
