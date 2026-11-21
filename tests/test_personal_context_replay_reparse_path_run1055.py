"""Personal Context replay SQLite paths reject Windows reparse-point entries."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark import personal_context_replay_ledger as replay


def _reparse_stat(*, directory: bool):
    mode = stat.S_IFDIR if directory else stat.S_IFREG
    return SimpleNamespace(
        st_mode=mode | 0o700,
        st_nlink=1,
        st_file_attributes=0x400,
    )


def test_reparse_policy_rebinding_is_rejected_before_lstat(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "_REPARSE_POINT_ATTRIBUTE", 0)

    def forbidden_lstat(path):
        raise AssertionError("filesystem inspected after replay policy drift")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="path admission changed"):
        replay._check_path(tmp_path / "context.sqlite3", create=True)


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_reparse_metadata_fails_closed(attributes):
    info = SimpleNamespace(
        st_mode=stat.S_IFDIR | 0o700,
        st_file_attributes=attributes,
    )
    with pytest.raises(replay.OfflineContextReplayRejected, match="reparse metadata is malformed"):
        replay._is_reparse_point(info)


def test_absent_platform_attribute_uses_non_reparse_default():
    info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700)
    assert replay._is_reparse_point(info) is False


def test_reparse_ancestor_is_rejected_before_ledger_access(tmp_path, monkeypatch):
    target = tmp_path / "context.sqlite3"
    original_lstat = Path.lstat

    def lstat(path):
        if path == tmp_path:
            return _reparse_stat(directory=True)
        if path == target:
            raise AssertionError("ledger leaf inspected through reparse ancestor")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="ancestor is unsafe"):
        replay._check_path(target, create=True)


def test_reparse_database_leaf_is_rejected(tmp_path, monkeypatch):
    target = tmp_path / "context.sqlite3"
    original_lstat = Path.lstat

    def lstat(path):
        if path == target:
            return _reparse_stat(directory=False)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="existing or aliased"):
        replay._check_path(target, create=False)


def test_reparse_sqlite_sidecar_is_rejected(tmp_path, monkeypatch):
    target = tmp_path / "context.sqlite3"
    target.write_bytes(b"synthetic sqlite placeholder")
    sidecar = target.with_name(target.name + "-wal")
    original_lstat = Path.lstat

    def lstat(path):
        if path == sidecar:
            return _reparse_stat(directory=False)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="sidecar"):
        replay._check_path(target, create=False)

def test_stat_module_rebinding_is_rejected_before_lstat(tmp_path, monkeypatch):
    monkeypatch.setattr(replay, "stat", SimpleNamespace())

    def forbidden_lstat(path):
        raise AssertionError("filesystem inspected after stat module substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="stat policy changed"):
        replay._check_path(tmp_path / "context.sqlite3", create=True)


@pytest.mark.parametrize("predicate", ("S_ISDIR", "S_ISREG", "S_ISLNK"))
def test_stat_predicate_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch, predicate,
):
    monkeypatch.setattr(replay.stat, predicate, lambda mode: False)

    def forbidden_lstat(path):
        raise AssertionError("filesystem inspected after stat predicate substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="stat policy changed"):
        replay._check_path(tmp_path / "context.sqlite3", create=True)


def test_stat_predicate_rebinding_during_metadata_read_is_rejected(
    tmp_path, monkeypatch,
):
    target = tmp_path / "context.sqlite3"
    original_lstat = Path.lstat
    leaf_inspected = False

    class MutatingMetadata:
        @property
        def st_mode(self):
            monkeypatch.setattr(replay.stat, "S_ISDIR", lambda mode: True)
            return stat.S_IFDIR | 0o700

    def lstat(path):
        nonlocal leaf_inspected
        if path == tmp_path:
            return MutatingMetadata()
        if path == target:
            leaf_inspected = True
            raise AssertionError("leaf inspected after metadata policy drift")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(replay.OfflineContextReplayRejected, match="stat policy changed"):
        replay._check_path(target, create=True)
    assert leaf_inspected is False


def test_reparse_metadata_callback_cannot_replace_stat_predicate(monkeypatch):
    class MutatingMetadata:
        @property
        def st_file_attributes(self):
            monkeypatch.setattr(replay.stat, "S_ISLNK", lambda mode: False)
            return 0

        @property
        def st_mode(self):
            return stat.S_IFREG | 0o600

    with pytest.raises(replay.OfflineContextReplayRejected, match="stat policy changed"):
        replay._is_reparse_point(MutatingMetadata())

