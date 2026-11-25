"""Run1360: Personal Context replay path pins stat classifiers."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from ark import personal_context_replay_ledger as replay


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_replacement_is_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("stat substitution reached filesystem inspection")

    with monkeypatch.context() as patch:
        patch.setattr(replay.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(tmp_path / "context.sqlite3", create=True)


def test_stat_module_replacement_is_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("stat module substitution reached filesystem inspection")

    with monkeypatch.context() as patch:
        patch.setattr(replay, "stat", object())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(tmp_path / "context.sqlite3", create=True)


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_replacement_from_lstat_is_denied_after_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(replay.stat, name, lambda *_args: True)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(tmp_path / "context.sqlite3", create=True)


def test_stat_module_replacement_from_lstat_is_denied_after_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(replay, "stat", object())
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(tmp_path / "context.sqlite3", create=True)


def test_missing_database_callback_cannot_replace_stat_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite3"
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == target:
            patch.setattr(
                replay.stat,
                "S_ISREG",
                lambda *_args: True,
            )
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(target, create=True)

    assert not target.exists()


def test_missing_sidecar_callback_cannot_replace_stat_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite3"
    target.write_bytes(b"synthetic context ledger marker")
    sidecar = target.with_name(target.name + "-wal")
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == sidecar:
            patch.setattr(
                replay.stat,
                "S_ISREG",
                lambda *_args: True,
            )
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(target, create=False)

    assert target.read_bytes() == b"synthetic context ledger marker"


def test_original_stat_policy_keeps_valid_paths_admissible(tmp_path: Path) -> None:
    target = tmp_path / "context.sqlite3"
    target.write_bytes(b"synthetic context ledger marker")

    assert replay._check_path(target, create=False) == target


class _ReparseMetadata:
    def __init__(self, mode: int, attributes: int = 0x400) -> None:
        self.st_mode = mode
        self.st_file_attributes = attributes
        self.st_nlink = 1


def test_windows_reparse_ancestor_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite3"
    original_lstat = Path.lstat

    def synthetic_lstat(path: Path):
        if path == tmp_path:
            return _ReparseMetadata(stat.S_IFDIR | 0o700)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", synthetic_lstat)
        with pytest.raises(replay.OfflineContextReplayRejected, match="ancestor is unsafe"):
            replay._check_path(target, create=True)


def test_windows_reparse_main_database_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite3"
    target.write_bytes(b"synthetic context ledger marker")
    original_lstat = Path.lstat

    def synthetic_lstat(path: Path):
        if path == target:
            return _ReparseMetadata(stat.S_IFREG | 0o600)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", synthetic_lstat)
        with pytest.raises(replay.OfflineContextReplayRejected, match="existing or aliased"):
            replay._check_path(target, create=False)


def test_windows_reparse_sqlite_sidecar_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite3"
    target.write_bytes(b"synthetic context ledger marker")
    sidecar = target.with_name(target.name + "-wal")
    original_lstat = Path.lstat

    def synthetic_lstat(path: Path):
        if path == sidecar:
            return _ReparseMetadata(stat.S_IFREG | 0o600)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", synthetic_lstat)
        with pytest.raises(replay.OfflineContextReplayRejected, match="sidecar"):
            replay._check_path(target, create=False)


def test_reparse_metadata_accessor_cannot_replace_stat_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            return stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            patch.setattr(replay.stat, "S_ISLNK", lambda *_args: False)
            return 0

    original_lstat = Path.lstat

    def synthetic_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", synthetic_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(tmp_path / "context.sqlite3", create=True)


def test_reparse_attribute_mask_is_pinned_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("reparse policy substitution reached filesystem inspection")

    with monkeypatch.context() as patch:
        patch.setattr(replay, "_REPARSE_POINT_ATTRIBUTE", 0)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay._check_path(tmp_path / "context.sqlite3", create=True)
