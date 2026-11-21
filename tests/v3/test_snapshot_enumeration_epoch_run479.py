"""Local-only manifest directory enumeration and alias guard regressions."""

from __future__ import annotations

import pytest

import ark.learning.identity as identity


def _source_tree(tmp_path):
    learning = tmp_path / "src" / "ark" / "learning"
    learning.mkdir(parents=True)
    (learning / "execution.py").write_text("one", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("project", encoding="utf-8")
    return learning


def test_static_nested_snapshot_is_stable_and_canonical(tmp_path):
    root = tmp_path / "snapshot"
    nested = root / "weights"
    nested.mkdir(parents=True)
    (root / "config.json").write_bytes(b"config")
    (nested / "model.safetensors").write_bytes(b"fixture")
    rows = identity.directory_file_identities(root)
    assert [row.path for row in rows] == ["config.json", "weights/model.safetensors"]
    assert rows == identity.directory_file_identities(root)


def test_new_file_during_hash_does_not_disappear_from_manifest(tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    root.mkdir()
    (root / "a.bin").write_bytes(b"a")
    original = identity._hash_file

    def insert(path):
        result = original(path)
        (root / "b.bin").write_bytes(b"b")
        return result

    monkeypatch.setattr(identity, "_hash_file", insert)
    with pytest.raises(ValueError, match="entries changed"):
        identity.directory_file_identities(root)


def test_removed_empty_directory_during_hash_is_detected(tmp_path, monkeypatch):
    root = tmp_path / "snapshot"
    root.mkdir()
    empty = root / "empty"
    empty.mkdir()
    (root / "file.bin").write_bytes(b"a")
    original = identity._hash_file

    def remove(path):
        result = original(path)
        empty.rmdir()
        return result

    monkeypatch.setattr(identity, "_hash_file", remove)
    with pytest.raises(ValueError, match="entries changed"):
        identity.directory_file_identities(root)


def test_symlinked_directory_fails_even_without_nested_files(tmp_path):
    root = tmp_path / "snapshot"
    root.mkdir()
    (root / "file.bin").write_bytes(b"data")
    target = tmp_path / "actual"
    target.mkdir()
    alias = root / "hidden"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this runner")
    with pytest.raises(ValueError, match="symlink"):
        identity.directory_file_identities(root)


def test_runtime_code_tree_refuses_late_module_insertion(tmp_path, monkeypatch):
    learning = _source_tree(tmp_path)
    original = identity._hash_file

    def insert(path):
        result = original(path)
        if path.name == "pyproject.toml":
            (learning / "late_module.py").write_bytes(b"new module")
        return result

    monkeypatch.setattr(identity, "_hash_file", insert)
    with pytest.raises(ValueError, match="entries changed"):
        identity.build_code_tree_identity(tmp_path)


def test_runtime_code_tree_refuses_unhashed_symlink_directory(tmp_path):
    learning = _source_tree(tmp_path)
    target = tmp_path / "outside"
    target.mkdir()
    alias = learning / "outside"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this runner")
    with pytest.raises(ValueError, match="symlink"):
        identity.build_code_tree_identity(tmp_path)


def test_runtime_code_manifest_remains_deterministic_for_clean_tree(tmp_path):
    _source_tree(tmp_path)
    result = identity.build_code_tree_identity(tmp_path)
    assert result == identity.build_code_tree_identity(tmp_path)
    assert len(result["manifest_sha256"]) == 64
