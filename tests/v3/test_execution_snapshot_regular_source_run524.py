"""V3 local snapshot must originate from a stable regular file, not an alias.

No GPU, model, training adapter, protected evaluation or network is used.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.learning import execution as mod


def test_regular_noncanonical_input_remains_accepted(tmp_path):
    source = tmp_path / "snapshot.json"
    source.write_bytes(b'{ "z" : false, "a" : [1,2] }')
    assert mod.load_snapshot(source) == {"z": False, "a": [1, 2]}


def test_directory_is_not_accepted_as_snapshot(tmp_path):
    with pytest.raises(ValueError, match="regular local file"):
        mod.load_snapshot(tmp_path)


def test_symbolic_link_source_is_rejected(tmp_path):
    target = tmp_path / "real.json"
    target.write_bytes(b'{"authorization":false}')
    alias = tmp_path / "alias.json"
    try:
        alias.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("creating symlinks is not permitted on this runner")
    with pytest.raises(ValueError, match="regular local file"):
        mod.load_snapshot(alias)


def test_fifo_is_rejected_without_opening_or_blocking(tmp_path):
    if not hasattr(os, "mkfifo"):
        pytest.skip("named pipes are not available on this platform")
    source = tmp_path / "snapshot.fifo"
    os.mkfifo(source)
    with pytest.raises(ValueError, match="regular local file"):
        mod.load_snapshot(source)


def test_oversized_file_fails_before_any_open(tmp_path, monkeypatch):
    source = tmp_path / "oversized.json"
    source.write_bytes(b"x" * 1_048_577)

    def forbidden_open(self, *args, **kwargs):
        raise AssertionError("oversized source must fail before opening")

    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError, match="JSON byte budget"):
        mod.load_snapshot(source)


def test_inode_swap_between_lstat_and_open_is_rejected(tmp_path, monkeypatch):
    source = tmp_path / "snapshot.json"
    other = tmp_path / "different.json"
    source.write_bytes(b'{"x": 1}')
    other.write_bytes(b'{"x": 2}')
    original_open = Path.open

    def switched(self, *args, **kwargs):
        if self == source and args and args[0] == "rb":
            other.replace(source)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", switched)
    with pytest.raises(ValueError, match="source changed before JSON decode"):
        mod.load_snapshot(source)


def test_symlink_swap_after_decode_is_rejected_even_if_same_inode(
    tmp_path, monkeypatch,
):
    source = tmp_path / "snapshot.json"
    hardlink = tmp_path / "still-original.json"
    probe = tmp_path / "symlink-probe"
    source.write_bytes(b'{"x": 1}')
    try:
        os.link(source, hardlink)
        probe.symlink_to(hardlink)
    except (OSError, NotImplementedError):
        pytest.skip("local link creation is not available on this runner")
    probe.unlink()
    original = mod.json.loads

    def switched(*args, **kwargs):
        decoded = original(*args, **kwargs)
        source.unlink()
        source.symlink_to(hardlink)
        return decoded

    monkeypatch.setattr(mod.json, "loads", switched)
    with pytest.raises(ValueError, match="source changed during JSON decode"):
        mod.load_snapshot(source)
