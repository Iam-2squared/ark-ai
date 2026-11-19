"""Run1001: reject Windows name-surrogate reparse points before descent."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import ark.learning.identity as identity


def _fake_project(tmp_path: Path) -> Path:
    learning = tmp_path / "src" / "ark" / "learning"
    learning.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'ark-fixture'\n", encoding="utf-8",
    )
    (learning / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    return learning


class _EntryProxy:
    def __init__(self, entry, reparse_path: Path, reparse_flag: int):
        self._entry = entry
        self._reparse_path = reparse_path
        self._reparse_flag = reparse_flag

    @property
    def path(self):
        return self._entry.path

    def is_symlink(self):
        # A Windows directory junction need not be reported as a symlink.
        return self._entry.is_symlink()

    def stat(self, *, follow_symlinks=True):
        info = self._entry.stat(follow_symlinks=follow_symlinks)
        if Path(self._entry.path) != self._reparse_path:
            return info
        return type("SyntheticReparseStat", (), {
            "st_mode": info.st_mode,
            "st_dev": info.st_dev,
            "st_ino": info.st_ino,
            "st_nlink": info.st_nlink,
            "st_size": info.st_size,
            "st_mtime_ns": info.st_mtime_ns,
            "st_ctime_ns": info.st_ctime_ns,
            "st_file_attributes": self._reparse_flag,
        })()


class _ScandirProxy:
    def __init__(self, entries):
        self._entries = entries

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __iter__(self):
        return iter(self._entries)


def test_directory_reparse_point_is_rejected_before_target_scandir(
    tmp_path, monkeypatch,
):
    learning = _fake_project(tmp_path)
    junction = learning / "external-junction"
    junction.mkdir()
    (junction / "must-not-be-enumerated.py").write_text(
        "PRIVATE_FIXTURE = True\n", encoding="utf-8",
    )

    # Simulate the Windows FILE_ATTRIBUTE_REPARSE_POINT bit on a no-follow
    # DirEntry.stat result without requiring a privileged real junction.
    flag = 0x400
    monkeypatch.setattr(identity, "_FILE_ATTRIBUTE_REPARSE_POINT", flag)
    original_scandir = os.scandir
    scanned_targets = []

    def scandir(path):
        path = Path(path)
        if path == junction:
            scanned_targets.append(path)
        with original_scandir(path) as entries:
            proxies = [
                _EntryProxy(entry, junction, flag)
                for entry in entries
            ]
        return _ScandirProxy(proxies)

    monkeypatch.setattr(identity.os, "scandir", scandir)

    with pytest.raises(ValueError, match="reparse-point entry"):
        identity.build_code_tree_identity(tmp_path)

    assert scanned_targets == []
