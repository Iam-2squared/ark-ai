"""Run1401: proactive SQLite path policy rejects aliases and reparse points.

Only synthetic temporary paths and metadata are used. No notification,
external action, trusted clock, consent or real scheduler dispatch is involved.
"""

from __future__ import annotations

import stat as statlib
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.proactive_synthetic_review as proactive
from ark.proactive_state_ledger import SyntheticProactiveStateLedger


def _metadata(mode: int, *, attributes: object = 0, links: int = 1):
    return SimpleNamespace(
        st_mode=mode,
        st_nlink=links,
        st_file_attributes=attributes,
    )


def _replace_path_policy(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[str],
) -> None:
    def hostile(name: str):
        def reject(*_args: object, **_kwargs: object) -> bool:
            calls.append(name)
            raise AssertionError("replacement proactive path predicate executed")

        return reject

    is_dir = hostile("S_ISDIR")
    is_link = hostile("S_ISLNK")
    is_regular = hostile("S_ISREG")
    file_type = hostile("S_IFMT")

    def fake_reparse(_info: object) -> bool:
        calls.append("reparse")
        raise AssertionError("replacement proactive reparse classifier executed")

    fake_sidecars: tuple[str, ...] = ()
    fake_stat = SimpleNamespace(
        S_ISDIR=is_dir,
        S_ISLNK=is_link,
        S_ISREG=is_regular,
        S_IFMT=file_type,
        FILE_ATTRIBUTE_REPARSE_POINT=0x800,
    )
    forged_epoch = (
        proactive._ORIGINAL_OS,
        proactive._ORIGINAL_FSENCODE,
        proactive._ORIGINAL_MAX_SQLITE_PATH_BYTES,
        fake_stat,
        is_dir,
        is_link,
        is_regular,
        file_type,
        0x800,
        fake_reparse,
        fake_sidecars,
    )
    monkeypatch.setattr(proactive, "stat", fake_stat)
    monkeypatch.setattr(proactive, "_ORIGINAL_STAT", fake_stat)
    monkeypatch.setattr(proactive, "_ORIGINAL_STAT_S_ISDIR", is_dir)
    monkeypatch.setattr(proactive, "_ORIGINAL_STAT_S_ISLNK", is_link)
    monkeypatch.setattr(proactive, "_ORIGINAL_STAT_S_ISREG", is_regular)
    monkeypatch.setattr(proactive, "_ORIGINAL_STAT_IFMT", file_type)
    monkeypatch.setattr(proactive, "_FILE_ATTRIBUTE_REPARSE_POINT", 0x800)
    monkeypatch.setattr(proactive, "_ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT", 0x800)
    monkeypatch.setattr(proactive, "_is_reparse_point", fake_reparse)
    monkeypatch.setattr(proactive, "_ORIGINAL_REPARSE_POINT_CHECK", fake_reparse)
    monkeypatch.setattr(proactive, "_SQLITE_SIDECARS", fake_sidecars)
    monkeypatch.setattr(proactive, "_ORIGINAL_SQLITE_SIDECARS", fake_sidecars)
    monkeypatch.setattr(
        proactive,
        "_ORIGINAL_PROACTIVE_PATH_POLICY_EPOCH",
        forged_epoch,
    )


def test_joint_stat_aliases_and_policy_epoch_are_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _replace_path_policy(monkeypatch, calls)

    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected before proactive path denial")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="proactive path admission policy changed",
    ):
        proactive._refuse_aliased_proactive_path(tmp_path / "new-trigger.sqlite")

    assert calls == []


def test_sidecar_suffix_vector_cannot_be_replaced_with_equal_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(list(proactive._SQLITE_SIDECARS))
    assert replacement == proactive._SQLITE_SIDECARS
    assert replacement is not proactive._SQLITE_SIDECARS
    with monkeypatch.context() as patch:
        patch.setattr(proactive, "_SQLITE_SIDECARS", replacement)
        with pytest.raises(
            proactive.SyntheticTriggerRejected,
            match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "new-trigger.sqlite")


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
            _replace_path_policy(monkeypatch, calls)
            return NoModeRead()
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", reentrant_lstat)
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="proactive path admission policy changed",
    ):
        proactive._refuse_aliased_proactive_path(tmp_path / "new-trigger.sqlite")

    assert calls == []


def test_reparse_point_parent_is_rejected_before_sqlite_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "trigger.sqlite"
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == tmp_path:
            return _metadata(statlib.S_IFDIR | 0o700, attributes=0x400)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="reparse-point or nondirectory parent",
    ):
        proactive._refuse_aliased_proactive_path(path)

    assert not path.exists()


def test_reparse_point_main_file_is_rejected_before_sqlite_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "trigger.sqlite"
    path.write_bytes(b"synthetic marker")
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == path:
            return _metadata(statlib.S_IFREG | 0o600, attributes=0x400)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="SQLite file or reparse point",
    ):
        proactive._refuse_aliased_proactive_path(path)


def test_reparse_point_sidecar_is_rejected_before_sqlite_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "trigger.sqlite"
    path.write_bytes(b"synthetic marker")
    sidecar = path.with_name(path.name + "-wal")
    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == sidecar:
            return _metadata(statlib.S_IFREG | 0o600, attributes=0x400)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="sidecar or reparse point",
    ):
        proactive._refuse_aliased_proactive_path(path)


def test_unlinked_regular_sidecar_gets_only_one_bounded_recheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "trigger.sqlite"
    path.write_bytes(b"synthetic marker")
    sidecar = path.with_name(path.name + "-journal")
    original_lstat = Path.lstat
    sidecar_calls = 0

    def lstat(candidate: Path):
        nonlocal sidecar_calls
        if candidate == sidecar:
            sidecar_calls += 1
            if sidecar_calls == 1:
                return _metadata(
                    statlib.S_IFREG | 0o600,
                    links=0,
                )
            raise FileNotFoundError
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    proactive._refuse_aliased_proactive_path(path)
    assert sidecar_calls == 2


def test_reentrant_reparse_metadata_accessor_cannot_restore_path_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class ReentrantMetadata:
        st_mode = statlib.S_IFDIR | 0o700
        st_nlink = 1

        @property
        def st_file_attributes(self):
            _replace_path_policy(monkeypatch, calls)
            return 0

    original_lstat = Path.lstat

    def lstat(candidate: Path):
        if candidate == tmp_path:
            return ReentrantMetadata()
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="proactive path admission policy changed",
    ):
        proactive._refuse_aliased_proactive_path(tmp_path / "new-trigger.sqlite")

    assert calls == []


def test_healthy_trigger_and_proactive_state_ledgers_remain_local_and_deny_only(
    tmp_path: Path,
) -> None:
    trigger = proactive.SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    state = SyntheticProactiveStateLedger(tmp_path / "state.sqlite")

    assert trigger.count() == 0
    assert state.count() == 0
