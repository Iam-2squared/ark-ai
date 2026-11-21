"""No content access, path creation or authorization from local source pins."""

from __future__ import annotations

import os
from dataclasses import FrozenInstanceError

import pytest

from ark.disconnected_local_source_pin import (
    DisconnectedSourcePin,
    DisconnectedSourceRejected,
    capture_disconnected_source,
    review_disconnected_source,
)


def source(tmp_path):
    file = tmp_path / "synthetic.sqlite3"
    file.write_bytes(b"synthetic fixture only")
    return file


def test_pin_stable_restart_no_authority(tmp_path):
    file = source(tmp_path)
    pin = capture_disconnected_source(file)
    assert review_disconnected_source(file, pin) == pin
    assert len(pin.path_sha256) == 64
    assert "synthetic.sqlite3" not in repr(pin)
    assert not pin.independently_attested
    assert not pin.contents_verified
    assert not pin.memory_release_authorized
    assert not pin.file_mutation_authorized
    with pytest.raises(FrozenInstanceError):
        pin.file_size = 99


def test_file_replacement_same_bytes_changes_inode(tmp_path):
    file = source(tmp_path)
    pin = capture_disconnected_source(file)
    replacement = tmp_path / "replacement"
    replacement.write_bytes(file.read_bytes())
    os.replace(replacement, file)
    with pytest.raises(DisconnectedSourceRejected, match="identity"):
        review_disconnected_source(file, pin)


def test_file_size_change_rejected(tmp_path):
    file = source(tmp_path)
    pin = capture_disconnected_source(file)
    file.write_bytes(b"now changed")
    with pytest.raises(DisconnectedSourceRejected, match="identity"):
        review_disconnected_source(file, pin)


def test_hardlink_not_admitted(tmp_path):
    file = source(tmp_path)
    pin = capture_disconnected_source(file)
    sibling = tmp_path / "additional-link"
    os.link(file, sibling)
    with pytest.raises(DisconnectedSourceRejected, match="singly linked"):
        capture_disconnected_source(file)
    with pytest.raises(DisconnectedSourceRejected, match="singly linked"):
        review_disconnected_source(file, pin)


def test_symlink_source_and_ancestor_rejected(tmp_path):
    file = source(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(file)
    with pytest.raises(DisconnectedSourceRejected, match="singly linked"):
        capture_disconnected_source(alias)
    nested = tmp_path / "nested"
    nested.mkdir()
    child = nested / "file.db"
    child.write_bytes(b"fixture")
    parent_link = tmp_path / "parent_link"
    parent_link.symlink_to(nested, target_is_directory=True)
    with pytest.raises(DisconnectedSourceRejected, match="ancestor"):
        capture_disconnected_source(parent_link / "file.db")


def test_deleted_file_not_recreated(tmp_path):
    file = source(tmp_path)
    pin = capture_disconnected_source(file)
    file.unlink()
    with pytest.raises(DisconnectedSourceRejected, match="unavailable"):
        review_disconnected_source(file, pin)
    assert not file.exists()


def test_parent_replacement_is_rejected(tmp_path):
    folder = tmp_path / "snapshot"
    folder.mkdir()
    file = folder / "store.db"
    file.write_bytes(b"fixture")
    pin = capture_disconnected_source(file)
    os.rename(folder, tmp_path / "moved")
    folder.mkdir()
    file.write_bytes(b"fixture")
    with pytest.raises(DisconnectedSourceRejected, match="identity"):
        review_disconnected_source(file, pin)


@pytest.mark.parametrize("invalid", [
    "relative.db", None, True, 1, [],
])
def test_wrong_path_type_rejected(invalid):
    with pytest.raises(DisconnectedSourceRejected):
        capture_disconnected_source(invalid)


def test_dotdot_component_rejected(tmp_path):
    file = source(tmp_path)
    path = tmp_path / "sub" / ".." / file.name
    with pytest.raises(DisconnectedSourceRejected):
        capture_disconnected_source(path)


@pytest.mark.parametrize("invalid", [
    None, True, object(), {},
    DisconnectedSourcePin("a" * 64, "b" * 64, True, 1, 2, 3, 4, 5),
    DisconnectedSourcePin("A" * 64, "b" * 64, 1, 1, 2, 3, 4, 5),
    DisconnectedSourcePin("a" * 64, "b" * 64, 1, -1, 2, 3, 4, 5),
])
def test_invalid_retained_shape_rejected(tmp_path, invalid):
    file = source(tmp_path)
    with pytest.raises(DisconnectedSourceRejected):
        review_disconnected_source(file, invalid)


def test_reflected_retained_mutation_during_scan_rejected(tmp_path, monkeypatch):
    file = source(tmp_path)
    pin = capture_disconnected_source(file)
    actual = os.lstat
    import ark.disconnected_local_source_pin as module

    def injected(path):
        object.__setattr__(pin, "file_inode", pin.file_inode + 1)
        return actual(path)

    monkeypatch.setattr(module.os, "lstat", injected)
    with pytest.raises(DisconnectedSourceRejected, match="retained file identity changed"):
        review_disconnected_source(file, pin)


def test_never_reads_file_content(tmp_path, monkeypatch):
    file = source(tmp_path)
    import builtins

    def forbidden(*args, **kwargs):
        raise AssertionError("file data must never be opened")

    monkeypatch.setattr(builtins, "open", forbidden)
    pin = capture_disconnected_source(file)
    assert review_disconnected_source(file, pin) == pin
