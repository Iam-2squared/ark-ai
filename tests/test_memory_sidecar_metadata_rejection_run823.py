"""Path-free SQLite sidecar rejection diagnostics on disposable fixtures only.

The metadata explanation must never turn a fail-closed path fence into a
retry or expose the local private database path, owner, or row contents.
"""

from __future__ import annotations

import os
import stat

import pytest

from ark.memory import MemorySchemaError
from ark.memory.sqlite_store import _require_safe_memory_path


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("kind", ("directory", "symlink", "hardlink"))
def test_unsafe_sidecar_rejection_includes_only_type_and_link_metadata(
    tmp_path, suffix: str, kind: str,
) -> None:
    # Deliberately not a real database. Validation must reject *before*
    # SQLite attempts any opening or parsing of retained private data.
    main = tmp_path / "private-owner-not-for-logs.sqlite"
    main.write_bytes(b"synthetic main metadata")
    sidecar = main.with_name(main.name + suffix)
    outside = tmp_path / "outside-private-not-for-logs"
    outside.write_bytes(b"synthetic unrelated bytes")
    if kind == "directory":
        sidecar.mkdir()
        expected_type = stat.S_IFDIR
        expected_links = sidecar.lstat().st_nlink
    elif kind == "symlink":
        try:
            sidecar.symlink_to(outside)
        except (OSError, NotImplementedError):
            pytest.skip("symlink unavailable")
        expected_type = stat.S_IFLNK
        expected_links = sidecar.lstat().st_nlink
    else:
        try:
            os.link(outside, sidecar)
        except (OSError, NotImplementedError):
            pytest.skip("hardlink unavailable")
        expected_type = stat.S_IFREG
        expected_links = 2

    saved_main = main.read_bytes()
    saved_outside = outside.read_bytes()
    with pytest.raises(MemorySchemaError, match="sidecar path is not a single regular file") as caught:
        _require_safe_memory_path(main, create=False)
    message = str(caught.value)
    assert f"suffix={suffix}" in message
    assert f"file_type={expected_type:#o}" in message
    assert f"link_count={expected_links}" in message
    assert str(tmp_path) not in message
    assert main.name not in message
    assert outside.name not in message
    assert main.read_bytes() == saved_main
    assert outside.read_bytes() == saved_outside


def test_regular_synthetic_sidecar_remains_accepted_without_sqlite_open(tmp_path) -> None:
    main = tmp_path / "synthetic.sqlite"
    main.write_bytes(b"not a SQLite database")
    (tmp_path / "synthetic.sqlite-wal").write_bytes(b"regular metadata")
    _require_safe_memory_path(main, create=False)


def test_orphan_sidecar_still_refused_without_leaking_path(tmp_path) -> None:
    main = tmp_path / "private-orphan.sqlite"
    (tmp_path / "private-orphan.sqlite-shm").write_bytes(b"retained synthetic bytes")
    with pytest.raises(MemorySchemaError, match="orphaned") as caught:
        _require_safe_memory_path(main, create=True)
    assert str(tmp_path) not in str(caught.value)
    assert not main.exists()
