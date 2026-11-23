"""Windows junction/reparse-point rejection in local V3 identity manifests."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.learning.identity as identity


def _reparse_directory_stat():
    # A Windows directory junction is a directory reparse point, not a POSIX
    # symlink. Keep S_ISDIR true and expose FILE_ATTRIBUTE_REPARSE_POINT.
    return SimpleNamespace(
        st_mode=stat.S_IFDIR | 0o755,
        st_file_attributes=0x400,
    )


def test_reparse_attribute_is_detected_without_symlink_mode():
    info = _reparse_directory_stat()
    assert stat.S_ISDIR(info.st_mode)
    assert not stat.S_ISLNK(info.st_mode)
    assert identity._is_reparse_point(info) is True


def test_directory_walk_rejects_reparse_entry_before_advancing(
    tmp_path, monkeypatch,
):
    root = tmp_path / "snapshot"
    root.mkdir()
    junction = root / "redirect"
    scanned = []

    class _OneEntryScandir:
        def __enter__(self):
            return iter((entry,))

        def __exit__(self, exc_type, exc, traceback):
            return False

    def entry_stat(*, follow_symlinks):
        assert follow_symlinks is False
        return _reparse_directory_stat()

    entry = SimpleNamespace(path=str(junction), stat=entry_stat)

    def guarded_scandir(path):
        current = Path(path)
        scanned.append(current)
        assert current == root, "enumeration advanced into a reparse directory"
        return _OneEntryScandir()

    original_lstat = Path.lstat

    def lstat(path):
        if path == junction:
            raise AssertionError("path metadata was read before no-follow classification")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="symlink entry"):
        identity._snapshot_entries(root, _scandir=guarded_scandir)

    assert scanned == [root]


def test_file_identity_rejects_reparse_ancestor_before_open(
    tmp_path, monkeypatch,
):
    parent = tmp_path / "junction-parent"
    parent.mkdir()
    payload = parent / "artifact.bin"
    payload.write_bytes(b"synthetic-local-payload")
    original_lstat = Path.lstat

    def lstat(path):
        if path == parent:
            return _reparse_directory_stat()
        return original_lstat(path)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("identity file opened through a reparse ancestor")

    monkeypatch.setattr(Path, "lstat", lstat)
    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError, match="symlinked identity file ancestors"):
        identity.file_identity(payload)


@pytest.mark.skipif(os.name != "nt", reason="Windows directory junction integration")
def test_real_windows_directory_junction_is_rejected(tmp_path):
    root = tmp_path / "snapshot"
    target = tmp_path / "outside"
    root.mkdir()
    target.mkdir()
    (target / "payload.bin").write_bytes(b"synthetic-local-payload")
    junction = root / "redirect"
    command = f'mklink /J "{junction}" "{target}"'
    result = subprocess.run(
        ["cmd.exe", "/c", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("runner could not create a disposable directory junction")
    with pytest.raises(ValueError, match="reparse-point"):
        identity.directory_file_identities(root)
