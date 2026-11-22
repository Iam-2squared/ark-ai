"""Run1108: detached V3 packet-file review pins stat classification policy.

Synthetic metadata and temporary packet files only. No compute, Candidate,
protected evaluation, external service or authorization is opened.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization_packet_file_review as mod


@pytest.mark.parametrize("predicate", ("S_ISREG", "S_ISLNK"))
def test_stat_predicate_rebinding_is_rejected_before_path_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, predicate: str,
) -> None:
    target = tmp_path / "review.json"

    def forbidden_lstat(_path: Path):
        raise AssertionError("path inspected after stat policy substitution")

    with monkeypatch.context() as patch:
        patch.setattr(mod.stat, predicate, lambda _mode: False)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="review packet reparse-point guard changed",
        ):
            mod._read_exact_local_packet(target)


def test_stat_module_rebinding_is_rejected_before_path_inspection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("path inspected after stat module substitution")

    with monkeypatch.context() as patch:
        patch.setattr(mod, "stat", SimpleNamespace())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="review packet reparse-point guard changed",
        ):
            mod._read_exact_local_packet(tmp_path / "review.json")


def test_reparse_attribute_accessor_cannot_replace_symlink_classifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        @property
        def st_file_attributes(self) -> int:
            monkeypatch.setattr(mod.stat, "S_ISLNK", lambda _mode: False)
            return 0

        st_mode = stat.S_IFREG | 0o600

    with pytest.raises(
        mod.LocalPacketBindingRejected,
        match="review packet reparse-point guard changed",
    ):
        mod._is_reparse_point(ReentrantMetadata())


def test_mode_accessor_cannot_replace_regular_file_classifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            monkeypatch.setattr(mod.stat, "S_ISREG", lambda _mode: True)
            return stat.S_IFREG | 0o600

    with pytest.raises(
        mod.LocalPacketBindingRejected,
        match="review packet reparse-point guard changed",
    ):
        mod._is_regular_file(ReentrantMetadata())


def test_lstat_callback_replacement_is_rejected_before_os_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "review.json"
    target.write_bytes(b"synthetic packet marker")
    original_lstat = Path.lstat
    opened: list[bool] = []

    def switched_lstat(path: Path):
        info = original_lstat(path)
        if path == target:
            monkeypatch.setattr(mod.stat, "S_ISREG", lambda _mode: True)
        return info

    def forbidden_open(*_args, **_kwargs):
        opened.append(True)
        raise AssertionError("packet opened after stat policy substitution")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", switched_lstat)
        patch.setattr(mod.os, "open", forbidden_open)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="review packet reparse-point guard changed",
        ):
            mod._read_exact_local_packet(target)
    assert opened == []


def test_link_count_accessor_replacement_is_rejected_before_os_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "review.json"
    original_lstat = Path.lstat
    opened: list[bool] = []

    class ReentrantMetadata:
        st_mode = stat.S_IFREG | 0o600
        st_file_attributes = 0
        st_size = 24

        @property
        def st_nlink(self) -> int:
            monkeypatch.setattr(mod.stat, "S_ISREG", lambda _mode: True)
            return 1

    def synthetic_lstat(path: Path):
        if path == target:
            return ReentrantMetadata()
        return original_lstat(path)

    def forbidden_open(*_args, **_kwargs):
        opened.append(True)
        raise AssertionError("packet opened after metadata callback substitution")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", synthetic_lstat)
        patch.setattr(mod.os, "open", forbidden_open)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="review packet reparse-point guard changed",
        ):
            mod._read_exact_local_packet(target)
    assert opened == []


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_present_reparse_attribute_is_denied(attributes: object) -> None:
    metadata = SimpleNamespace(
        st_mode=stat.S_IFREG | 0o600,
        st_file_attributes=attributes,
    )
    with pytest.raises(
        mod.LocalPacketBindingRejected,
        match="review packet reparse metadata is malformed",
    ):
        mod._is_reparse_point(metadata)


def test_absent_platform_reparse_attribute_keeps_non_reparse_default() -> None:
    metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600)
    assert mod._is_reparse_point(metadata) is False


def test_fstat_callback_cannot_replace_classifier_before_packet_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "review.json"
    target.write_bytes(b"synthetic packet marker")
    original_fstat = mod.os.fstat
    original_fdopen = mod.os.fdopen
    reads: list[bool] = []

    class ReadSpy:
        def __init__(self, handle) -> None:
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.handle.__exit__(*args)

        def fileno(self) -> int:
            return self.handle.fileno()

        def read(self, *args, **kwargs):
            reads.append(True)
            return self.handle.read(*args, **kwargs)

    def tracked_fdopen(*args, **kwargs):
        return ReadSpy(original_fdopen(*args, **kwargs))

    def switched_fstat(descriptor: int):
        info = original_fstat(descriptor)
        monkeypatch.setattr(mod.stat, "S_ISREG", lambda _mode: True)
        return info

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "fdopen", tracked_fdopen)
        patch.setattr(mod.os, "fstat", switched_fstat)
        with pytest.raises(
            mod.LocalPacketBindingRejected,
            match="review packet reparse-point guard changed",
        ):
            mod._read_exact_local_packet(target)
    assert reads == []
