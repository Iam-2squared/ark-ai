"""Read-only V3 packet verification rejects Windows reparse-point paths."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_authorization_packet_file_review_run529 import _saved_packet

from ark.learning import authorization_packet_file_review as mod


def _reparse_stat(*, directory: bool):
    mode = stat.S_IFDIR if directory else stat.S_IFREG
    return SimpleNamespace(
        st_mode=mode | 0o755,
        st_file_attributes=0x400,
    )


def test_reparse_point_detection_is_not_limited_to_symlink_mode():
    info = _reparse_stat(directory=True)
    assert stat.S_ISDIR(info.st_mode)
    assert not stat.S_ISLNK(info.st_mode)
    assert mod._is_reparse_point(info) is True


def test_reparse_packet_file_is_denied_before_open(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    original_lstat = Path.lstat

    def lstat(candidate):
        if candidate == path:
            return _reparse_stat(directory=False)
        return original_lstat(candidate)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("reparse packet path reached os.open")

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(mod.os, "open", forbidden_open)
    with pytest.raises(mod.LocalPacketBindingRejected, match="path or byte budget denied"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )


def test_reparse_directory_ancestor_is_denied_before_open(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    parent = path.parent
    original_lstat = Path.lstat

    def lstat(candidate):
        if candidate == parent:
            return _reparse_stat(directory=True)
        return original_lstat(candidate)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("packet opened through a reparse-point ancestor")

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(mod.os, "open", forbidden_open)
    with pytest.raises(mod.LocalPacketBindingRejected, match="path or byte budget denied"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )


def test_reparse_ancestor_appearing_between_two_reads_is_denied(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    parent = path.parent
    original_lstat = Path.lstat
    parent_checks = 0

    def lstat(candidate):
        nonlocal parent_checks
        if candidate == parent:
            parent_checks += 1
            # First passive read remains ordinary. Simulate a junction
            # appearing before the independent final read.
            if parent_checks >= 5:
                return _reparse_stat(directory=True)
        return original_lstat(candidate)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(mod.LocalPacketBindingRejected, match="path or byte budget denied"):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
    assert parent_checks >= 5
