"""Windows reparse-point ancestors are denied before and after packet writes."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization


def _reparse_directory_stat():
    # A junction is a directory reparse point, not necessarily a symlink.
    return SimpleNamespace(
        st_mode=stat.S_IFDIR | 0o755,
        st_file_attributes=0x400,
    )


def test_reparse_directory_attribute_is_detected_without_symlink_mode():
    info = _reparse_directory_stat()
    assert stat.S_ISDIR(info.st_mode)
    assert not stat.S_ISLNK(info.st_mode)
    assert authorization._is_reparse_point(info) is True


def test_reparse_ancestor_is_rejected_before_exclusive_packet_open(
    tmp_path, monkeypatch,
):
    parent = tmp_path / "junction-parent"
    parent.mkdir()
    target = parent / "authorization-review.json"
    original_lstat = Path.lstat

    def lstat(path):
        if path == parent:
            return _reparse_directory_stat()
        return original_lstat(path)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("packet opened through a reparse-point ancestor")

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError, match="non-aliased"):
        authorization._write_new_authorization_packet(
            target,
            {"full_training_authorized": False},
        )
    assert not target.exists()


def test_reparse_ancestor_appearing_after_write_is_rejected_before_readback(
    tmp_path, monkeypatch,
):
    parent = tmp_path / "packet-parent"
    parent.mkdir()
    target = parent / "authorization-review.json"
    original_lstat = Path.lstat
    parent_checks = 0

    def lstat(path):
        nonlocal parent_checks
        if path == parent:
            parent_checks += 1
            # Initial path preflight sees a normal directory. The simulated
            # junction appears during the post-write custody recheck.
            if parent_checks >= 4:
                return _reparse_directory_stat()
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="alias or size changed"):
        authorization._write_new_authorization_packet(
            target,
            {"full_training_authorized": False},
        )
    assert target.exists()
    assert parent_checks >= 4
