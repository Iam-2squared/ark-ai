"""Run1400: Personal Context replay path policy is pinned across callbacks.

Only synthetic temporary SQLite paths and metadata are used. No context text,
consent, disclosure, notification, external effect or real dispatch is involved.
"""

from __future__ import annotations

import stat as statlib
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.personal_context_replay_ledger as replay


def _metadata(mode: int, *, attributes: object = 0):
    return SimpleNamespace(
        st_mode=mode,
        st_nlink=1,
        st_file_attributes=attributes,
    )


def _replace_stat_policy(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
) -> None:
    def hostile(name: str):
        def reject(*_args: object, **_kwargs: object) -> bool:
            calls.append(name)
            raise AssertionError("replacement context path predicate executed")

        return reject

    is_dir = hostile("S_ISDIR")
    is_link = hostile("S_ISLNK")
    is_regular = hostile("S_ISREG")
    file_type = hostile("S_IFMT")

    def fake_reparse(_info: object) -> bool:
        calls.append("reparse")
        raise AssertionError("replacement reparse classifier executed")

    fake_stat = SimpleNamespace(
        S_ISDIR=is_dir,
        S_ISLNK=is_link,
        S_ISREG=is_regular,
        S_IFMT=file_type,
        FILE_ATTRIBUTE_REPARSE_POINT=0x800,
    )
    forged_epoch = (
        replay._ORIGINAL_OS,
        replay._ORIGINAL_FSENCODE,
        replay._ORIGINAL_MAX_DB_PATH_BYTES,
        fake_stat,
        is_dir,
        is_link,
        is_regular,
        file_type,
        0x800,
        fake_reparse,
    )
    monkeypatch.setattr(replay, "stat", fake_stat)
    monkeypatch.setattr(replay, "_ORIGINAL_STAT", fake_stat)
    monkeypatch.setattr(replay, "_ORIGINAL_STAT_S_ISDIR", is_dir)
    monkeypatch.setattr(replay, "_ORIGINAL_STAT_S_ISLNK", is_link)
    monkeypatch.setattr(replay, "_ORIGINAL_STAT_S_ISREG", is_regular)
    monkeypatch.setattr(replay, "_ORIGINAL_STAT_IFMT", file_type)
    monkeypatch.setattr(replay, "_FILE_ATTRIBUTE_REPARSE_POINT", 0x800)
    monkeypatch.setattr(replay, "_ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT", 0x800)
    monkeypatch.setattr(replay, "_is_reparse_point", fake_reparse)
    monkeypatch.setattr(replay, "_ORIGINAL_REPARSE_POINT_CHECK", fake_reparse)
    monkeypatch.setattr(
        replay,
        "_ORIGINAL_CONTEXT_REPLAY_PATH_POLICY_EPOCH",
        forged_epoch,
    )


def test_joint_stat_aliases_and_epoch_are_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _replace_stat_policy(monkeypatch, calls)

    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected before path-policy denial")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay path admission policy changed",
    ):
        replay.DisconnectedContextReplayLedger(
            tmp_path / "new-context.sqlite",
            create=True,
        )

    assert calls == []


def test_reentrant_stat_epoch_replacement_is_denied_before_st_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class NoModeRead:
        @property
        def st_mode(self):
            raise AssertionError("metadata mode read after reentrant policy change")

    original_lstat = Path.lstat

    def reentrant_lstat(candidate: Path):
        if candidate == tmp_path:
            _replace_stat_policy(monkeypatch, calls)
            return NoModeRead()
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", reentrant_lstat)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay path admission policy changed",
    ):
        replay.DisconnectedContextReplayLedger(
            tmp_path / "new-context.sqlite",
            create=True,
        )

    assert calls == []


def test_reparse_point_ancestor_is_rejected_before_database_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "context.sqlite"
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == tmp_path:
            return _metadata(statlib.S_IFDIR | 0o700, attributes=0x400)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="reparse-point ancestor",
    ):
        replay.DisconnectedContextReplayLedger(path, create=True)

    assert not path.exists()


def test_reparse_point_database_leaf_is_rejected_before_sqlite_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "context.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == path:
            return _metadata(statlib.S_IFREG | 0o600, attributes=0x400)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="reparse-point context ledger path",
    ):
        ledger.witness()


def test_reparse_point_sqlite_sidecar_is_rejected_before_reopen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "context.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    sidecar = path.with_name(path.name + "-wal")
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == sidecar:
            return _metadata(statlib.S_IFREG | 0o600, attributes=0x400)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="sidecar is not a single regular non-reparse file",
    ):
        ledger.witness()


def test_reentrant_reparse_metadata_accessor_is_rechecked_before_classification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class ReentrantMetadata:
        st_mode = statlib.S_IFDIR | 0o700
        st_nlink = 1

        @property
        def st_file_attributes(self):
            _replace_stat_policy(monkeypatch, calls)
            return 0

    def lstat(candidate: Path):
        if candidate == tmp_path:
            return ReentrantMetadata()
        return Path.lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay path admission policy changed",
    ):
        replay.DisconnectedContextReplayLedger(
            tmp_path / "new-context.sqlite",
            create=True,
        )

    assert calls == []
