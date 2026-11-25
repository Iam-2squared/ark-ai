"""A dangling Windows reparse-point leaf is rejected before packet create."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization


def test_dangling_reparse_leaf_is_rejected_before_exclusive_open(
    tmp_path, monkeypatch,
):
    target = tmp_path / "authorization-review.json"
    original_lstat = Path.lstat
    original_exists = Path.exists
    original_is_symlink = Path.is_symlink

    def lstat(candidate):
        if candidate == target:
            # A Windows reparse entry can have regular-file mode and not be
            # reported as a POSIX symlink, while its target is unavailable.
            return SimpleNamespace(
                st_mode=stat.S_IFREG | 0o600,
                st_file_attributes=0x400,
                st_nlink=1,
            )
        return original_lstat(candidate)

    def forbidden_follow(candidate):
        if candidate == target:
            raise AssertionError("final leaf followed before no-follow admission")
        return original_exists(candidate)

    def forbidden_symlink_probe(candidate):
        if candidate == target:
            raise AssertionError("final leaf classified by symlink mode only")
        return original_is_symlink(candidate)

    def forbidden_open(*_args, **_kwargs):
        raise AssertionError("packet reached exclusive create through reparse leaf")

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(Path, "exists", forbidden_follow)
    monkeypatch.setattr(Path, "is_symlink", forbidden_symlink_probe)
    monkeypatch.setattr(Path, "open", forbidden_open)

    with pytest.raises(ValueError, match="new non-aliased file"):
        authorization._write_new_authorization_packet(
            target,
            {"candidate_created": False},
        )
