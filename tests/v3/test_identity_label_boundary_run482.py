"""Free-only file identity label validation; no actual model or GPU activity."""

from __future__ import annotations

import pytest

import ark.learning.identity as identity


class StringCarrier(str):
    pass


@pytest.mark.parametrize("label", [
    False,
    True,
    1,
    b"file.py",
    object(),
    "",
    ".",
    "..",
    "/file.py",
    "a/../file.py",
    "a/./file.py",
    "a//file.py",
    "a/",
    "a\\file.py",
    "C:/file.py",
    "f\0ile.py",
    "f\nile.py",
    "x" * 4097,
    StringCarrier("ordinary.py"),
])
def test_invalid_label_is_denied_before_file_read(tmp_path, monkeypatch, label):
    file = tmp_path / "model.txt"
    file.write_bytes(b"fixture-only")
    def must_not_hash(_):
        raise AssertionError("invalid label must fail before file hashing")
    monkeypatch.setattr(identity, "_hash_file", must_not_hash)
    with pytest.raises(ValueError, match="identity label"):
        identity.file_identity(file, label=label)


@pytest.mark.parametrize("label", [
    "model.txt",
    "src/ark/learning/identity.py",
    "nested/a.b",
])
def test_valid_relative_labels_preserve_original_digest(tmp_path, label):
    file = tmp_path / "model.txt"
    file.write_bytes(b"fixture-only")
    result = identity.file_identity(file, label=label)
    assert result.path == label
    assert result.bytes == len(b"fixture-only")
    assert len(result.sha256) == 64
    assert result.symlink is False


def test_default_label_is_file_basename(tmp_path):
    file = tmp_path / "simple.txt"
    file.write_bytes(b"data")
    assert identity.file_identity(file).path == "simple.txt"


def test_relative_parent_component_in_real_path_still_refused(tmp_path):
    file = tmp_path / "sub" / ".." / "simple.txt"
    (tmp_path / "sub").mkdir()
    (tmp_path / "simple.txt").write_bytes(b"fixture-only")
    with pytest.raises(ValueError, match="parent aliases"):
        identity.file_identity(file, label="safe.txt")
