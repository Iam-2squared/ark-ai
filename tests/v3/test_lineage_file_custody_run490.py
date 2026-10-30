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
