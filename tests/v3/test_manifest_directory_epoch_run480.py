"""V3 local manifest refuses same-name directory-tree epoch replacement.

Only free, local synthetic files are touched; no models/tools are downloaded
or run. Metadata epochs are not adversarial file-system snapshots.
"""

from __future__ import annotations

import os

import pytest

import ark.learning.identity as identity


def _fixture(tmp_path):
    root = tmp_path / "snapshot"
    nested = root / "weights"
    nested.mkdir(parents=True)
    (nested / "part.safetensors").write_bytes(b"same bytes")
    return root


def test_static_nested_directory_epoch_is_deterministic(tmp_path):
    root = _fixture(tmp_path)
    first = identity.directory_file_identities(root)
    assert first == identity.directory_file_identities(root)
    assert first[0].path == "weights/part.safetensors"


def test_replaced_root_with_identical_listing_is_denied(tmp_path, monkeypatch):
    root = _fixture(tmp_path)
    moved = tmp_path / "old-tree"
    original = identity.file_identity
    swapped = False

    def switch_after_hash(path, *, label=None):
        nonlocal swapped
        result = original(path, label=label)
        if not swapped:
            swapped = True
            root.rename(moved)
            _fixture(tmp_path)
        return result

    monkeypatch.setattr(identity, "file_identity", switch_after_hash)
    with pytest.raises(ValueError, match="identit|entries"):
        identity.directory_file_identities(root)
    assert swapped


def test_replaced_nested_directory_with_same_bytes_is_denied(tmp_path, monkeypatch):
    root = _fixture(tmp_path)
    nested = root / "weights"
    moved = tmp_path / "old-weights"
    original = identity.file_identity

    def switch_nested_after_hash(path, *, label=None):
        result = original(path, label=label)
        nested.rename(moved)
        nested.mkdir()
        (nested / "part.safetensors").write_bytes(b"same bytes")
        return result

    monkeypatch.setattr(identity, "file_identity", switch_nested_after_hash)
    with pytest.raises(ValueError, match="identit|entries"):
        identity.directory_file_identities(root)


def test_root_metadata_change_after_hash_is_denied(tmp_path, monkeypatch):
    root = _fixture(tmp_path)
    original = identity.file_identity

    def change_root_mtime(path, *, label=None):
        result = original(path, label=label)
        before = root.stat()
        os.utime(
            root,
            ns=(before.st_atime_ns, before.st_mtime_ns + 10_000_000_000),
        )
        return result

    monkeypatch.setattr(identity, "file_identity", change_root_mtime)
    with pytest.raises(ValueError, match="identit|entries"):
        identity.directory_file_identities(root)


def test_runtime_python_tree_same_name_replacement_is_denied(tmp_path, monkeypatch):
    learning = tmp_path / "src" / "ark" / "learning"
    learning.mkdir(parents=True)
    (learning / "entry.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[build-system]", encoding="utf-8")
    moved = tmp_path / "old-learning"
    original = identity.file_identity
    swapped = False

    def switch_after_last_hash(path, *, label=None):
        nonlocal swapped
        result = original(path, label=label)
        if path.name == "entry.py":
            swapped = True
            learning.rename(moved)
            learning.mkdir()
            (learning / "entry.py").write_text("x = 1", encoding="utf-8")
        return result

    monkeypatch.setattr(identity, "file_identity", switch_after_last_hash)
    with pytest.raises(ValueError, match="identit|entries"):
        identity.build_code_tree_identity(tmp_path)
    assert swapped
