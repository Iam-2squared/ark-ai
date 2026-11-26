"""Proactive SQLite path admission pins policy across reentrant callbacks.

Only temporary paths and synthetic metadata are used. No scheduler, private
state database, notification, consent or external effect is exercised.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.proactive_synthetic_review as proactive
from ark.proactive_synthetic_review import SyntheticTriggerRejected


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat predicate substitution")

    with monkeypatch.context() as patch:
        patch.setattr(proactive.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_stat_module_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat module substitution")

    with monkeypatch.context() as patch:
        patch.setattr(proactive, "stat", object())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_filesystem_encoding_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after encoding substitution")

    with monkeypatch.context() as patch:
        patch.setattr(proactive.os, "fsencode", lambda _path: b"")
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_reparse_mask_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after reparse-mask substitution")

    with monkeypatch.context() as patch:
        patch.setattr(proactive, "_PROACTIVE_REPARSE_POINT_ATTRIBUTE", 0x800)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_sidecar_vector_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after sidecar-vector substitution")

    with monkeypatch.context() as patch:
        patch.setattr(proactive, "_SQLITE_SIDECARS", ())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(proactive.stat, name, lambda *_args: True)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_stat_module_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(proactive, "stat", object())
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_stat_policy_rebinding_on_missing_main_path_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "proactive.sqlite"
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == target:
            patch.setattr(proactive.stat, "S_ISREG", lambda *_args: True)
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(target)


def test_stat_policy_rebinding_from_mode_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            patch.setattr(proactive.stat, "S_ISDIR", lambda *_args: True)
            return stat.S_IFDIR | 0o700

        st_file_attributes = 0
        st_nlink = 1

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_stat_policy_rebinding_from_windows_attribute_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        st_mode = stat.S_IFDIR | 0o700
        st_nlink = 1

        @property
        def st_file_attributes(self) -> int:
            patch.setattr(proactive.stat, "S_ISLNK", lambda *_args: True)
            return 0

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(tmp_path / "proactive.sqlite")


def test_stat_policy_rebinding_from_main_link_count_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "proactive.sqlite"
    target.write_bytes(b"synthetic main marker")

    class ReentrantMetadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0

        @property
        def st_nlink(self) -> int:
            patch.setattr(proactive.stat, "S_ISREG", lambda *_args: False)
            return 1

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == target:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(target)


def test_stat_policy_rebinding_from_sidecar_link_count_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "proactive.sqlite"
    sidecar = target.with_name(target.name + "-wal")
    target.write_bytes(b"synthetic main marker")
    sidecar.write_bytes(b"synthetic sidecar marker")

    class ReentrantMetadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0

        @property
        def st_nlink(self) -> int:
            patch.setattr(proactive.stat, "S_ISREG", lambda *_args: False)
            return 1

    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        if path == sidecar:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(target)


def test_stat_policy_rebinding_from_sidecar_recheck_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "proactive.sqlite"
    sidecar = target.with_name(target.name + "-wal")
    target.write_bytes(b"synthetic main marker")
    sidecar.write_bytes(b"synthetic sidecar marker")
    original_lstat = Path.lstat
    calls = 0

    class Metadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0

        def __init__(self, links: int) -> None:
            self.st_nlink = links

    def reentrant_lstat(path: Path):
        nonlocal calls
        if path == sidecar:
            calls += 1
            if calls == 2:
                patch.setattr(proactive.stat, "S_ISREG", lambda *_args: False)
            return Metadata(0 if calls == 1 else 1)
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive path admission policy changed",
        ):
            proactive._refuse_aliased_proactive_path(target)
        assert calls == 2


def test_windows_reparse_ancestor_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    parent = tmp_path / "junction"
    parent.mkdir()
    target = parent / "proactive.sqlite"
    original_lstat = Path.lstat

    def marked_lstat(path: Path):
        if path == parent:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o700,
                st_nlink=1,
                st_file_attributes=0x400,
            )
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive parent path"):
            proactive._refuse_aliased_proactive_path(target)


def test_windows_reparse_main_file_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "proactive.sqlite"
    target.write_bytes(b"synthetic main marker")
    original_lstat = Path.lstat

    def marked_lstat(path: Path):
        if path == target:
            return SimpleNamespace(
                st_mode=stat.S_IFREG | 0o600,
                st_nlink=1,
                st_file_attributes=0x400,
            )
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite file"):
            proactive._refuse_aliased_proactive_path(target)


def test_windows_reparse_sidecar_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    target = tmp_path / "proactive.sqlite"
    sidecar = target.with_name(target.name + "-wal")
    target.write_bytes(b"synthetic main marker")
    sidecar.write_bytes(b"synthetic sidecar marker")
    original_lstat = Path.lstat

    def marked_lstat(path: Path):
        if path == sidecar:
            return SimpleNamespace(
                st_mode=stat.S_IFREG | 0o600,
                st_nlink=1,
                st_file_attributes=0x400,
            )
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", marked_lstat)
        with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite sidecar"):
            proactive._refuse_aliased_proactive_path(target)
