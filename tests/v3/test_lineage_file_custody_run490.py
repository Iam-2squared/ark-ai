"""Local-only V3 artifact byte hashing rejects ambiguous filesystem sources.

Does not generate Candidate bytes, authorize training, or certify a trusted OS.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from ark.learning.lineage import hash_file


def test_regular_local_artifact_hash_is_exact_and_stable(tmp_path):
    path = tmp_path / "artifact.bin"
    data = b"ARK-local-lineage-test\x00" * 5
    path.write_bytes(data)
    assert hash_file(path) == (hashlib.sha256(data).hexdigest(), len(data))


def test_relative_parent_traversal_is_not_an_artifact_identity(tmp_path):
    path = tmp_path / "inside"
    path.mkdir()
    (tmp_path / "item.bin").write_bytes(b"item")
    with pytest.raises(ValueError, match="lineage hash path"):
        hash_file(path / ".." / "item.bin")


def test_symlinked_parent_is_denied_even_when_final_file_is_regular(tmp_path):
    root = tmp_path / "real"
    root.mkdir()
    (root / "artifact.bin").write_bytes(b"identity")
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(root, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this host")
    with pytest.raises(ValueError, match="lineage hash path"):
        hash_file(alias / "artifact.bin")


def test_multi_link_artifact_is_not_a_single_custody_source(tmp_path):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"identity")
    alias = tmp_path / "alias.bin"
    try:
        os.link(path, alias)
    except OSError:
        pytest.skip("hardlink creation unavailable on this host")
    with pytest.raises(ValueError, match="lineage hash path"):
        hash_file(path)


def test_swapping_path_between_preflight_and_open_fails_closed(tmp_path, monkeypatch):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"small")
    original = Path.open
    swapped = False

    def swap_before_open(self, *args, **kwargs):
        nonlocal swapped
        if self == path and not swapped:
            swapped = True
            path.unlink()
            path.write_bytes(b"different replacement artifact with a different length")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", swap_before_open)
    with pytest.raises(ValueError, match="lineage hash path"):
        hash_file(path)
    assert swapped


def test_string_subclass_and_path_subclass_not_accepted_as_identity(tmp_path):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"test")

    class StringPath(str):
        pass

    with pytest.raises(ValueError, match="lineage hash path"):
        hash_file(StringPath(str(path)))


def test_same_size_replacement_cannot_impersonate_opened_file(tmp_path, monkeypatch):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"ORIGINAL")
    substitute = tmp_path / "substitute.bin"
    substitute.write_bytes(b"REPLACED")
    old = path.stat()
    os.utime(substitute, ns=(old.st_atime_ns, old.st_mtime_ns))
    original_open = Path.open
    replaced = False

    def swap_before_open(self, *args, **kwargs):
        nonlocal replaced
        if self == path and not replaced:
            replaced = True
            substitute.replace(path)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", swap_before_open)
    with pytest.raises(ValueError, match="lineage hash path changed before reading"):
        hash_file(path)
    assert replaced


def test_descriptor_must_refer_to_preflight_file(tmp_path, monkeypatch):
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"unchanged")
    monkeypatch.setattr(os.path, "samestat", lambda before, opened: False)
    with pytest.raises(ValueError, match="lineage hash path changed before reading"):
        hash_file(path)


@pytest.mark.skipif(os.name != "nt", reason="Windows path/fd ctime semantics")
def test_windows_path_vs_handle_ctime_difference_is_not_a_file_swap(tmp_path, monkeypatch):
    path = tmp_path / "artifact.bin"
    data = b"stable byte identity"
    path.write_bytes(data)
    original_fstat = os.fstat

    class WindowsHandleStat:
        def __init__(self, stat_result):
            for field in (
                "st_dev", "st_ino", "st_mode", "st_nlink", "st_size",
                "st_mtime_ns", "st_ctime_ns",
            ):
                setattr(self, field, getattr(stat_result, field))
            self.st_ctime_ns += 1

    monkeypatch.setattr(
        os, "fstat", lambda fd: WindowsHandleStat(original_fstat(fd)),
    )
    assert hash_file(path) == (hashlib.sha256(data).hexdigest(), len(data))
