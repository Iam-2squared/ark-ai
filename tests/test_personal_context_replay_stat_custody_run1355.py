"""Run1355: Personal Context replay path pins stat classifiers."""

from __future__ import annotations

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
