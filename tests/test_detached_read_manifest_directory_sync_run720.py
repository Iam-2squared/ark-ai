"""POSIX name-durability failures do not grant READ replay authority."""

from __future__ import annotations

import errno
import os
import stat

import pytest

from ark.agency import disconnected_read_input_manifest as manifest

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
INPUTS = ((STEP, "b" * 64),)


@pytest.mark.skipif(os.name != "posix", reason="POSIX directory-fd fsync")
def test_write_once_syncs_both_file_and_parent_directory(tmp_path, monkeypatch):
    original_fsync = os.fsync
    synced = []

    def tracked(fd):
        synced.append(stat.S_ISDIR(os.fstat(fd).st_mode))
        return original_fsync(fd)

    monkeypatch.setattr(manifest.os, "fsync", tracked)
    path = tmp_path / "manifest.json"
    result = manifest.write_read_input_manifest_once(path, REQUEST, INPUTS)

    assert synced == [False, True]
    assert manifest.load_read_input_manifest(
        path, expected_sha256=result.artifact_sha256,
    ) == result
    assert result.backend_dispatched is False
    assert result.automatic_replay_authorized is False


@pytest.mark.skipif(os.name != "posix", reason="POSIX directory-fd fsync")
def test_parent_directory_sync_failure_quarantines_created_name(tmp_path, monkeypatch):
    original_fsync = os.fsync
    synced = []

    def refuse_directory(fd):
        directory = stat.S_ISDIR(os.fstat(fd).st_mode)
        synced.append(directory)
        if directory:
            raise OSError(errno.EIO, "injected parent directory fsync failure")
        return original_fsync(fd)

    monkeypatch.setattr(manifest.os, "fsync", refuse_directory)
    path = tmp_path / "possibly_unpublished.json"
    with pytest.raises(manifest.ReadInputManifestRejected, match="parent sync refused"):
        manifest.write_read_input_manifest_once(path, REQUEST, INPUTS)

    assert synced == [False, True]
    assert path.exists()  # Never auto-unlink or overwrite UNKNOWN publication.
    first_bytes = path.read_bytes()
    with pytest.raises(manifest.ReadInputManifestRejected, match="creation refused"):
        manifest.write_read_input_manifest_once(path, REQUEST, INPUTS)
    assert path.read_bytes() == first_bytes
    diagnostic = manifest.load_read_input_manifest(path)
    assert diagnostic.independent_custody_proven is False
    assert diagnostic.external_result_proven is False
