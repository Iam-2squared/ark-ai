"""Free-only V3 identity hashing must bind bytes to the opened inode.

A file with the same length at another path must not be hashed accidentally.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ark.learning import identity


def test_hash_refuses_redirected_file_handle_even_when_path_epoch_is_stable(
    tmp_path, monkeypatch,
):
    intended = tmp_path / "base.safetensors"
    diverted = tmp_path / "replacement.safetensors"
    intended.write_bytes(b"original")
    diverted.write_bytes(b"spoofed!")
    assert intended.stat().st_size == diverted.stat().st_size

    normal_open = Path.open

    def redirected_open(self, mode="r", *args, **kwargs):
        if self == intended and mode == "rb":
            return normal_open(diverted, mode, *args, **kwargs)
        return normal_open(self, mode, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", redirected_open)
        with pytest.raises(ValueError, match="changed during hashing"):
            identity.file_identity(intended)

    verified = identity.file_identity(intended)
    assert verified.sha256 == hashlib.sha256(b"original").hexdigest()
    assert verified.bytes == len(b"original")


def test_descriptor_check_preserves_normal_local_manifest(tmp_path):
    file = tmp_path / "tool.bin"
    file.write_bytes(b"offline-only tool fixture")
    result = identity.file_identity(file, label="tools/tool.bin")
    assert result.sha256 == hashlib.sha256(b"offline-only tool fixture").hexdigest()
    assert result.path == "tools/tool.bin"
    assert result.symlink is False
