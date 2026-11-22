"""Windows no-follow DirEntry/Path metadata compatibility stays fail-closed."""

from __future__ import annotations

import stat

import pytest

import ark.learning.identity as identity


def _epoch(
    *,
    mode: int,
    size: int = 0,
    mtime: int = 100,
    device: int = 1,
    inode: int = 2,
    ctime: int = 300,
    links: int = 1,
) -> tuple[int, ...]:
    return (device, inode, mode, size, mtime, ctime, links)


def test_windows_directory_comparison_ignores_cross_api_allocation_and_permission_drift():
    entry = _epoch(
        mode=stat.S_IFDIR | 0o755,
        size=4096,
        mtime=100,
        device=1,
        inode=2,
        ctime=300,
        links=1,
    )
    path = _epoch(
        mode=stat.S_IFDIR | 0o700,
        size=0,
        # Directory mtime is not stable across Windows DirEntry/Path APIs.
        mtime=5_000_100,
        device=9,
        inode=8,
        ctime=900,
        links=2,
    )

    assert identity._entry_metadata_matches_path(
        entry, path, windows=True, is_dir=True,
    )


def test_windows_directory_comparison_rejects_type_drift():
    entry = _epoch(mode=stat.S_IFDIR | 0o755, size=4096, mtime=100)
    path = _epoch(mode=stat.S_IFREG | 0o600, size=0, mtime=100)

    assert not identity._entry_metadata_matches_path(
        entry, path, windows=True, is_dir=True,
    )


def test_windows_regular_file_comparison_keeps_type_size_and_mtime():
    entry = _epoch(
        mode=stat.S_IFREG | 0o644,
        size=12,
        mtime=100,
        device=1,
        inode=2,
        ctime=300,
        links=1,
    )
    path = _epoch(
        mode=stat.S_IFREG | 0o600,
        size=12,
        mtime=100,
        device=9,
        inode=8,
        ctime=900,
        links=2,
    )

    assert identity._entry_metadata_matches_path(
        entry, path, windows=True, is_dir=False,
    )
    assert not identity._entry_metadata_matches_path(
        entry, _epoch(mode=stat.S_IFREG | 0o600, size=13, mtime=100),
        windows=True, is_dir=False,
    )
    assert not identity._entry_metadata_matches_path(
        entry, _epoch(mode=stat.S_IFREG | 0o600, size=12, mtime=101),
        windows=True, is_dir=False,
    )


def test_posix_comparison_keeps_the_complete_metadata_epoch():
    entry = _epoch(mode=stat.S_IFDIR | 0o755, size=4096, mtime=100)
    assert identity._entry_metadata_matches_path(
        entry, entry, windows=False, is_dir=True,
    )
    changed = _epoch(
        mode=stat.S_IFDIR | 0o755, size=4096, mtime=100,
        device=1, inode=2, ctime=301, links=1,
    )
    assert not identity._entry_metadata_matches_path(
        entry, changed, windows=False, is_dir=True,
    )


def test_replaced_import_original_file_type_classifier_is_denied(monkeypatch):
    original = identity.stat.S_IFMT
    monkeypatch.setattr(identity.stat, "S_IFMT", lambda mode: original(mode))

    with pytest.raises(ValueError, match="reparse-point policy changed"):
        identity._entry_metadata_matches_path(
            _epoch(mode=stat.S_IFDIR | 0o755),
            _epoch(mode=stat.S_IFDIR | 0o755),
            windows=True,
            is_dir=True,
        )
