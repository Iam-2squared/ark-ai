"""Synthetic read-only source seals have no auth, WAL or write capability."""

import os
from dataclasses import FrozenInstanceError

import pytest

from ark.disconnected_file_seal import (
    DisconnectedFileSeal,
    DisconnectedFileSealRejected,
    capture_disconnected_file_seal,
    review_disconnected_file_seal,
)


def fixture(tmp_path, content=b"Synthetic private fixture: no user bytes"):
    path = tmp_path / "sample.db"
    path.write_bytes(content)
    return path


def test_deterministic_two_pass_read_and_no_authority(tmp_path):
    path = fixture(tmp_path)
    seal = capture_disconnected_file_seal(path)
    assert review_disconnected_file_seal(path, seal) == seal
    assert seal.size_bytes == path.stat().st_size
    assert len(seal.source_sha256) == 64
    assert not seal.source_authenticated
    assert not seal.independent_custody_proven
    assert not seal.wal_snapshot_verified
    assert not seal.context_disclosure_authorized
    assert not seal.file_mutation_authorized
    assert str(path) not in repr(seal)
    with pytest.raises(FrozenInstanceError):
        seal.size_bytes = 999


def test_empty_file_allowed(tmp_path):
    path = fixture(tmp_path, b"")
    assert capture_disconnected_file_seal(path).size_bytes == 0


def test_changed_same_size_bytes_rejected(tmp_path):
    path = fixture(tmp_path, b"original")
    seal = capture_disconnected_file_seal(path)
    path.write_bytes(b"modified")
    with pytest.raises(DisconnectedFileSealRejected):
        review_disconnected_file_seal(path, seal)


def test_new_file_same_bytes_rejected(tmp_path):
    path = fixture(tmp_path)
    seal = capture_disconnected_file_seal(path)
    replacement = tmp_path / "replacement"
    replacement.write_bytes(path.read_bytes())
    os.replace(replacement, path)
    with pytest.raises(DisconnectedFileSealRejected):
        review_disconnected_file_seal(path, seal)


def test_deleted_file_not_recreated(tmp_path):
    path = fixture(tmp_path)
    seal = capture_disconnected_file_seal(path)
    path.unlink()
    with pytest.raises(DisconnectedFileSealRejected):
        review_disconnected_file_seal(path, seal)
    assert not path.exists()


def test_hardlink_disallowed(tmp_path):
    path = fixture(tmp_path)
    os.link(path, tmp_path / "hardlink")
    with pytest.raises(DisconnectedFileSealRejected, match="singly linked"):
        capture_disconnected_file_seal(path)


def test_symlink_source_disallowed(tmp_path):
    path = fixture(tmp_path)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(path)
    except (OSError, NotImplementedError):
        pytest.skip("symlink privilege unavailable")
    with pytest.raises(DisconnectedFileSealRejected):
        capture_disconnected_file_seal(alias)


def test_symlink_ancestor_disallowed(tmp_path):
    folder = tmp_path / "dir"
    folder.mkdir()
    path = folder / "db"
    path.write_bytes(b"fixture")
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(folder, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink privilege unavailable")
    with pytest.raises(DisconnectedFileSealRejected, match="ancestor"):
        capture_disconnected_file_seal(alias / "db")


def test_parent_replacement_rejected(tmp_path):
    folder = tmp_path / "original"
    folder.mkdir()
    path = folder / "db"
    path.write_bytes(b"fixture")
    seal = capture_disconnected_file_seal(path)
    folder.rename(tmp_path / "old")
    folder.mkdir()
    path.write_bytes(b"fixture")
    with pytest.raises(DisconnectedFileSealRejected):
        review_disconnected_file_seal(path, seal)


@pytest.mark.parametrize("bad", [None, True, 1, "relative", [], {}])
def test_invalid_paths(bad):
    with pytest.raises(DisconnectedFileSealRejected):
        capture_disconnected_file_seal(bad)


def test_dotdot_path_rejected(tmp_path):
    path = fixture(tmp_path)
    with pytest.raises(DisconnectedFileSealRejected):
        capture_disconnected_file_seal(tmp_path / "nested" / ".." / path.name)


def test_too_large_source_rejected(tmp_path):
    path = tmp_path / "large"
    with path.open("wb") as f:
        f.truncate(8 * 1024 * 1024 + 1)
    with pytest.raises(DisconnectedFileSealRejected, match="budget"):
        capture_disconnected_file_seal(path)


@pytest.mark.parametrize("bad", [
    None, True, object(), "abc",
    DisconnectedFileSeal("a" * 64, "b" * 64, "C" * 64, 1, 2, 3, 4, 5),
    DisconnectedFileSeal("a" * 64, "b" * 64, "c" * 64, True, 2, 3, 4, 5),
])
def test_invalid_retained_type_or_shape(tmp_path, bad):
    path = fixture(tmp_path)
    with pytest.raises(DisconnectedFileSealRejected):
        review_disconnected_file_seal(path, bad)


def test_detect_modified_during_read(tmp_path, monkeypatch):
    path = fixture(tmp_path, b"a" * 200000)
    import ark.disconnected_file_seal as module
    real_read = module.os.read
    fired = False

    def injected(fd, amount):
        nonlocal fired
        data = real_read(fd, amount)
        if not fired:
            fired = True
            with path.open("r+b") as f:
                f.seek(100000)
                f.write(b"X")
                f.flush()
                os.fsync(f.fileno())
        return data

    monkeypatch.setattr(module.os, "read", injected)
    with pytest.raises(DisconnectedFileSealRejected, match="changed"):
        capture_disconnected_file_seal(path)


def test_detect_retained_reflective_mutation(tmp_path, monkeypatch):
    path = fixture(tmp_path)
    seal = capture_disconnected_file_seal(path)
    import ark.disconnected_file_seal as module
    old = module._once

    def tamper(candidate):
        object.__setattr__(seal, "size_bytes", seal.size_bytes + 1)
        return old(candidate)

    monkeypatch.setattr(module, "_once", tamper)
    with pytest.raises(DisconnectedFileSealRejected, match="retained seal changed"):
        review_disconnected_file_seal(path, seal)


def test_seal_contains_no_payload_or_write_calls(tmp_path, monkeypatch):
    path = fixture(tmp_path)
    content = path.read_bytes()
    import ark.disconnected_file_seal as module

    def forbid(*args, **kwargs):
        raise AssertionError("source seal must not create/write files")

    monkeypatch.setattr(module.os, "write", forbid)
    seal = capture_disconnected_file_seal(path)
    assert content not in repr(seal).encode()
