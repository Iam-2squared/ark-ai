"""Personal Context replay ledger path policy survives reentrant metadata callbacks.

Only disposable temporary paths and synthetic metadata are used. No private
context rows, disclosure, consent or external effects are involved.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

import ark.personal_context_replay_ledger as replay
from ark.personal_context_replay_ledger import OfflineContextReplayRejected


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat predicate substitution")

    with monkeypatch.context() as patch:
        patch.setattr(replay.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(tmp_path / "context.sqlite", create=True)


def test_stat_module_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat module substitution")

    with monkeypatch.context() as patch:
        patch.setattr(replay, "stat", object())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(tmp_path / "context.sqlite", create=True)


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(replay.stat, name, lambda *_args: True)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(tmp_path / "context.sqlite", create=True)


def test_stat_module_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(replay, "stat", object())
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(tmp_path / "context.sqlite", create=True)


def test_stat_policy_rebinding_on_missing_leaf_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    target = tmp_path / "context.sqlite"

    def reentrant_lstat(path: Path):
        if path == target:
            patch.setattr(replay.stat, "S_ISREG", lambda *_args: True)
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(target, create=True)


def test_stat_policy_rebinding_from_mode_metadata_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            patch.setattr(replay.stat, "S_ISDIR", lambda *_args: True)
            return stat.S_IFDIR | 0o700

        st_nlink = 1
        st_file_attributes = 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(tmp_path / "context.sqlite", create=True)


def test_stat_policy_rebinding_from_windows_metadata_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    class ReentrantMetadata:
        st_mode = stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            patch.setattr(replay.stat, "S_ISLNK", lambda *_args: True)
            return 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            OfflineContextReplayRejected, match="path admission changed",
        ):
            replay._check_path(tmp_path / "context.sqlite", create=True)


def _reparse_info(mode: int):
    return type(
        "ReparseInfo", (),
        {"st_mode": mode, "st_nlink": 1, "st_file_attributes": 0x400},
    )()


def test_context_ledger_rejects_windows_reparse_ancestor_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "junction"
    parent.mkdir()
    target = parent / "context.sqlite"
    original_lstat = Path.lstat

    def marked_lstat(path: Path):
        if path == parent:
            return _reparse_info(stat.S_IFDIR | 0o700)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        with pytest.raises(OfflineContextReplayRejected, match="ancestor"):
            replay._check_path(target, create=True)


def test_context_ledger_rejects_windows_reparse_main_file_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite"
    target.write_bytes(b"synthetic ledger marker")
    original_lstat = Path.lstat

    def marked_lstat(path: Path):
        if path == target:
            return _reparse_info(stat.S_IFREG | 0o600)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        with pytest.raises(OfflineContextReplayRejected, match="aliased"):
            replay._check_path(target, create=False)


def test_context_ledger_rejects_windows_reparse_sidecar_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "context.sqlite"
    target.write_bytes(b"synthetic ledger marker")
    sidecar = target.with_name(target.name + "-wal")
    sidecar.write_bytes(b"synthetic sidecar marker")
    original_lstat = Path.lstat

    def marked_lstat(path: Path):
        if path == sidecar:
            return _reparse_info(stat.S_IFREG | 0o600)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        with pytest.raises(OfflineContextReplayRejected, match="sidecar"):
            replay._check_path(target, create=False)
