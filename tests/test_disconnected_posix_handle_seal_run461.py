"""Synthetic local files only; no real user files or external actions."""

from __future__ import annotations

import hashlib
import os
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from ark import disconnected_posix_handle_seal as module
from ark.disconnected_posix_handle_seal import (
    PosixHandleSealRejected,
    capture_posix_handle_seal,
    review_posix_handle_seal,
)


@pytest.fixture(autouse=True)
def _posix_only():
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        pytest.skip("POSIX descriptor-anchored fixture tests")


def _fixture(tmp_path: Path, payload: bytes = b"ARK fixture\x00\x01") -> Path:
    folder = tmp_path / "memory" / "events"
    folder.mkdir(parents=True)
    path = folder / "source.bin"
    path.write_bytes(payload)
    return path


def test_repeated_capture_is_deterministic_and_private(tmp_path):
    path = _fixture(tmp_path)
    first = capture_posix_handle_seal(path)
    assert capture_posix_handle_seal(path) == first
    assert first.content_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert first.size_bytes == len(path.read_bytes())
    assert path.read_bytes().decode("latin1") not in repr(first)
    assert "memory" not in repr(first)
    assert review_posix_handle_seal(path, first) == first


@pytest.mark.parametrize("capability", (
    "independent_custody_proven", "source_authenticated", "durable_snapshot_proven",
    "file_mutation_authorized", "tool_execution_authorized",
))
def test_no_authority_claim(tmp_path, capability):
    claim = capture_posix_handle_seal(_fixture(tmp_path))
    assert getattr(claim, capability) is False


def test_empty_file_allowed(tmp_path):
    assert capture_posix_handle_seal(_fixture(tmp_path, b"")).size_bytes == 0


def test_maximum_size_allowed(tmp_path):
    path = _fixture(tmp_path, b"x" * (8 * 1024 * 1024))
    assert capture_posix_handle_seal(path).size_bytes == 8 * 1024 * 1024


def test_byte_budget_fails_before_read(tmp_path):
    path = _fixture(tmp_path, b"x" * (8 * 1024 * 1024 + 1))
    with pytest.raises(PosixHandleSealRejected, match="budget"):
        capture_posix_handle_seal(path)


@pytest.mark.parametrize("value", ("/tmp/data", Path("relative"), None, False, 42))
def test_exact_absolute_path_required(value):
    with pytest.raises(PosixHandleSealRejected, match="path"):
        capture_posix_handle_seal(value)


def test_parent_lexical_traversal_rejected(tmp_path):
    path = tmp_path / "memory" / ".." / "test.dat"
    with pytest.raises(PosixHandleSealRejected, match="path"):
        capture_posix_handle_seal(path)


def test_parent_symlink_rejected(tmp_path):
    target = _fixture(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(target.parent, target_is_directory=True)
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(alias / target.name)


def test_grandparent_symlink_rejected(tmp_path):
    target = _fixture(tmp_path)
    (tmp_path / "alias").symlink_to(target.parent.parent, target_is_directory=True)
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(tmp_path / "alias" / "events" / target.name)


def test_final_file_symlink_rejected(tmp_path):
    target = _fixture(tmp_path)
    alias = target.with_name("pointer")
    alias.symlink_to(target)
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(alias)


def test_hardlink_rejected(tmp_path):
    target = _fixture(tmp_path)
    second = target.with_name("hardlink")
    os.link(target, second)
    with pytest.raises(PosixHandleSealRejected, match="linked"):
        capture_posix_handle_seal(target)


def test_directory_as_file_rejected(tmp_path):
    folder = tmp_path / "folder"
    folder.mkdir()
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(folder)


def test_fifo_as_file_rejected(tmp_path):
    path = tmp_path / "pipe"
    os.mkfifo(path)
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(path)


def test_mutation_after_seal_rejected(tmp_path):
    path = _fixture(tmp_path)
    seal = capture_posix_handle_seal(path)
    path.write_bytes(b"different")
    with pytest.raises(PosixHandleSealRejected, match="differs"):
        review_posix_handle_seal(path, seal)


def test_same_bytes_replacement_rejected(tmp_path):
    path = _fixture(tmp_path)
    seal = capture_posix_handle_seal(path)
    replacement = path.with_name("new")
    replacement.write_bytes(path.read_bytes())
    os.replace(replacement, path)
    with pytest.raises(PosixHandleSealRejected, match="differs"):
        review_posix_handle_seal(path, seal)


def test_source_deletion_fails_closed(tmp_path):
    path = _fixture(tmp_path)
    seal = capture_posix_handle_seal(path)
    path.unlink()
    with pytest.raises(PosixHandleSealRejected):
        review_posix_handle_seal(path, seal)


def test_parent_retarget_while_reading_is_detected(tmp_path, monkeypatch):
    path = _fixture(tmp_path)
    real_read = module.os.read
    swapped = False

    def replace_parent_during_read(fd, size):
        nonlocal swapped
        chunk = real_read(fd, size)
        if not swapped:
            swapped = True
            original = path.parent
            original.rename(original.with_name("old-events"))
            original.symlink_to(original.with_name("old-events"), target_is_directory=True)
        return chunk

    monkeypatch.setattr(module.os, "read", replace_parent_during_read)
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(path)


def test_source_swap_while_reading_is_detected(tmp_path, monkeypatch):
    path = _fixture(tmp_path)
    real_read = module.os.read
    swapped = False

    def swap_source(fd, size):
        nonlocal swapped
        chunk = real_read(fd, size)
        if not swapped:
            swapped = True
            replacement = path.with_name("replacement")
            replacement.write_bytes(b"attacker")
            os.replace(replacement, path)
        return chunk

    monkeypatch.setattr(module.os, "read", swap_source)
    with pytest.raises(PosixHandleSealRejected):
        capture_posix_handle_seal(path)


def test_bad_retained_types_fail(tmp_path):
    path = _fixture(tmp_path)
    seal = capture_posix_handle_seal(path)
    for altered in (
        None, {}, replace(seal, content_sha256="oops"),
        replace(seal, size_bytes=True), replace(seal, inode=-1),
    ):
        with pytest.raises(PosixHandleSealRejected):
            review_posix_handle_seal(path, altered)


def test_retained_carrier_is_immutable(tmp_path):
    seal = capture_posix_handle_seal(_fixture(tmp_path))
    with pytest.raises(FrozenInstanceError):
        seal.size_bytes = 2


def test_unsupported_descriptor_mode_fails_closed(tmp_path, monkeypatch):
    path = _fixture(tmp_path)
    monkeypatch.setattr(module.os, "supports_dir_fd", set())
    with pytest.raises(PosixHandleSealRejected, match="unsupported"):
        capture_posix_handle_seal(path)
