"""Purely local V3 byte manifest path and read-epoch regressions."""

from __future__ import annotations

import os

import pytest

import ark.learning.identity as identity


def test_stable_local_file_identity_has_unchanged_manifest_shape(tmp_path):
    path = tmp_path / "tool.bin"
    path.write_bytes(b"fixed free-only fixture")
    first = identity.file_identity(path, label="tools/tool.bin")
    assert first == identity.file_identity(path, label="tools/tool.bin")
    assert first.bytes == len(b"fixed free-only fixture")
    assert first.symlink is False
    assert first.path == "tools/tool.bin"
    assert len(first.sha256) == 64


def test_mid_hash_file_content_rewrite_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "model.bin"
    path.write_bytes(b"initial")
    before = identity._hash_file

    def mutate(candidate):
        output = before(candidate)
        candidate.write_bytes(b"changed-by-fault-injection")
        return output

    monkeypatch.setattr(identity, "_hash_file", mutate)
    with pytest.raises(ValueError, match="changed during hashing"):
        identity.file_identity(path)


def test_mid_hash_atomic_path_replacement_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "weights.bin"
    replacement = tmp_path / "new.bin"
    path.write_bytes(b"original")
    replacement.write_bytes(b"replacement")
    before = identity._hash_file

    def swap(candidate):
        output = before(candidate)
        os.replace(replacement, candidate)
        return output

    monkeypatch.setattr(identity, "_hash_file", swap)
    with pytest.raises(ValueError, match="changed during hashing"):
        identity.file_identity(path)


def test_false_hash_byte_length_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "weights.bin"
    path.write_bytes(b"abc")
    monkeypatch.setattr(identity, "_hash_file", lambda _: ("a" * 64, 4))
    with pytest.raises(ValueError, match="changed during hashing"):
        identity.file_identity(path)


def test_missing_file_is_never_created(tmp_path):
    path = tmp_path / "not-a-model"
    with pytest.raises(ValueError, match="file"):
        identity.file_identity(path)
    assert not path.exists()


def test_parent_alias_path_is_rejected(tmp_path):
    path = tmp_path / "segment" / "file.bin"
    path.parent.mkdir()
    path.write_bytes(b"data")
    with pytest.raises(ValueError, match="parent aliases"):
        identity.file_identity(path.parent / ".." / "segment" / "file.bin")


def test_symlinked_ancestor_is_rejected(tmp_path):
    target = tmp_path / "real"
    target.mkdir()
    (target / "model.bin").write_bytes(b"bytes")
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported by this host")
    with pytest.raises(ValueError, match="ancestors"):
        identity.file_identity(alias / "model.bin")


def test_file_hardlink_alias_is_rejected(tmp_path):
    original = tmp_path / "original.bin"
    alias = tmp_path / "alias.bin"
    original.write_bytes(b"same underlying inode")
    try:
        os.link(original, alias)
    except (OSError, NotImplementedError):
        pytest.skip("hardlinks not supported by this host")
    with pytest.raises(ValueError, match="one regular-file link"):
        identity.file_identity(alias)
