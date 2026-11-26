"""Only synthetic temp-file SQLite identities; no actual user databases."""

from __future__ import annotations

import os
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from ark import disconnected_sqlite_sidecar_custody as module
from ark.disconnected_sqlite_sidecar_custody import (
    SQLiteSidecarCustodyRejected,
    capture_disconnected_sqlite_sidecars,
    review_disconnected_sqlite_sidecars,
)


@pytest.fixture(autouse=True)
def _posix_only():
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        pytest.skip("POSIX descriptor-relative SQLite fixture review only")


def _db(tmp_path):
    folder = tmp_path / "memory" / "store"
    folder.mkdir(parents=True)
    path = folder / "fixture.sqlite"
    path.write_bytes(b"synthetic fixture sqlite metadata")
    return path


def test_stable_absent_sidecars_and_no_authority(tmp_path):
    path = _db(tmp_path)
    first = capture_disconnected_sqlite_sidecars(path)
    assert first == capture_disconnected_sqlite_sidecars(path)
    assert first == review_disconnected_sqlite_sidecars(path, first)
    assert tuple(s.suffix for s in first.sidecars) == ("-wal", "-shm", "-journal")
    assert all(not s.present and s.identity_sha256 is None for s in first.sidecars)
    assert len(first.fingerprint) == 64
    for name in (
        "sqlite_transaction_atomicity_proven", "independent_witness_custody_proven",
        "stable_future_path_proven", "consent_verified", "tool_execution_authorized",
    ):
        assert getattr(first, name) is False
    assert str(path) not in repr(first)
    assert "synthetic fixture sqlite metadata" not in repr(first)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_sidecar_added_and_removed_are_detected(tmp_path, suffix):
    path = _db(tmp_path)
    empty = capture_disconnected_sqlite_sidecars(path)
    sidecar = Path(str(path) + suffix)
    sidecar.write_bytes(b"mock sidecar")
    with pytest.raises(SQLiteSidecarCustodyRejected, match="differs"):
        review_disconnected_sqlite_sidecars(path, empty)
    current = capture_disconnected_sqlite_sidecars(path)
    assert next(s for s in current.sidecars if s.suffix == suffix).present is True
    sidecar.unlink()
    with pytest.raises(SQLiteSidecarCustodyRejected, match="differs"):
        review_disconnected_sqlite_sidecars(path, current)
    assert capture_disconnected_sqlite_sidecars(path) == empty


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_sidecar_modified_and_replaced_are_detected(tmp_path, suffix):
    path = _db(tmp_path)
    sidecar = Path(str(path) + suffix)
    sidecar.write_bytes(b"fixture")
    baseline = capture_disconnected_sqlite_sidecars(path)
    sidecar.write_bytes(b"changed!")
    with pytest.raises(SQLiteSidecarCustodyRejected):
        review_disconnected_sqlite_sidecars(path, baseline)
    new = capture_disconnected_sqlite_sidecars(path)
    temp = sidecar.with_name(sidecar.name + ".tmp")
    temp.write_bytes(b"changed!")
    os.replace(temp, sidecar)
    with pytest.raises(SQLiteSidecarCustodyRejected):
        review_disconnected_sqlite_sidecars(path, new)


def test_main_same_bytes_atomic_replacement_detected(tmp_path):
    path = _db(tmp_path)
    baseline = capture_disconnected_sqlite_sidecars(path)
    temp = path.with_name("replacement")
    temp.write_bytes(path.read_bytes())
    os.replace(temp, path)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="differs"):
        review_disconnected_sqlite_sidecars(path, baseline)


def test_main_missing_is_not_recreated(tmp_path):
    path = _db(tmp_path)
    path.unlink()
    with pytest.raises(SQLiteSidecarCustodyRejected, match="missing"):
        capture_disconnected_sqlite_sidecars(path)
    assert not path.exists()


@pytest.mark.parametrize("suffix", ("", "-wal", "-shm", "-journal"))
def test_symlink_source_or_sidecar_rejected(tmp_path, suffix):
    path = _db(tmp_path)
    alias = Path(str(path) + suffix)
    if not suffix:
        alias.unlink()
    alias.symlink_to(tmp_path / "nonexistent")
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(path)


@pytest.mark.parametrize("suffix", ("", "-wal", "-shm", "-journal"))
def test_hardlink_source_or_sidecar_rejected(tmp_path, suffix):
    path = _db(tmp_path)
    aliased = Path(str(path) + suffix)
    if suffix:
        aliased.write_bytes(b"synthetic")
    os.link(aliased, aliased.with_name("alias" + suffix))
    with pytest.raises(SQLiteSidecarCustodyRejected, match="linked"):
        capture_disconnected_sqlite_sidecars(path)


def test_parent_and_grandparent_symlinks_rejected(tmp_path):
    path = _db(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(path.parent, target_is_directory=True)
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(alias / path.name)
    (tmp_path / "grandparent").symlink_to(path.parent.parent, target_is_directory=True)
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(tmp_path / "grandparent" / "store" / path.name)


def test_nested_parent_renamed_during_inspection_rejected(tmp_path, monkeypatch):
    path = _db(tmp_path)
    real_stat = module.os.stat
    changed = False

    def rename_during_stat(name, *args, **kwargs):
        nonlocal changed
        if not changed and name == path.name and kwargs.get("dir_fd") is not None:
            changed = True
            path.parent.rename(path.parent.with_name("moved"))
            path.parent.symlink_to(path.parent.with_name("moved"), target_is_directory=True)
        return real_stat(name, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", rename_during_stat)
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(path)


def test_sidecar_created_between_two_inspections_rejected(tmp_path, monkeypatch):
    path = _db(tmp_path)
    original = module._capture_once
    calls = 0

    def create_on_second(source):
        nonlocal calls
        calls += 1
        if calls == 2:
            Path(str(path) + "-wal").write_bytes(b"synthetic")
        return original(source)

    monkeypatch.setattr(module, "_capture_once", create_on_second)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="between inspections"):
        capture_disconnected_sqlite_sidecars(path)


def test_forged_or_mutated_retained_seal_rejected(tmp_path):
    path = _db(tmp_path)
    current = capture_disconnected_sqlite_sidecars(path)
    with pytest.raises(FrozenInstanceError):
        current.fingerprint = "f" * 64
    for invalid in (
        None, {}, replace(current, fingerprint="wrong"),
        replace(current, path_sha256="A" * 64),
        replace(current, sidecars=()),
        replace(current, sidecars=(replace(current.sidecars[0], present=True),)
                + current.sidecars[1:]),
        replace(current, sidecars=(replace(current.sidecars[0], suffix="-other"),)
                + current.sidecars[1:]),
    ):
        with pytest.raises(SQLiteSidecarCustodyRejected):
            review_disconnected_sqlite_sidecars(path, invalid)


@pytest.mark.parametrize("source", (None, True, 2, "file.sqlite", Path("relative")))
def test_invalid_exact_path_rejected(source):
    with pytest.raises(SQLiteSidecarCustodyRejected, match="Path"):
        capture_disconnected_sqlite_sidecars(source)


def test_invalid_traversal_and_overlong_path(tmp_path):
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(tmp_path / ".." / "fixture.sqlite")
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(Path("/" + "/".join(["folder"] * 1000)))


def test_directory_and_fifo_rejected(tmp_path):
    path = _db(tmp_path)
    path.unlink()
    path.mkdir()
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(path)
    path.rmdir()
    os.mkfifo(path)
    with pytest.raises(SQLiteSidecarCustodyRejected):
        capture_disconnected_sqlite_sidecars(path)


def test_over_budget_main_and_sidecar_rejected(tmp_path):
    path = _db(tmp_path)
    with path.open("wb") as output:
        output.truncate(64 * 1024 * 1024 + 1)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="budget"):
        capture_disconnected_sqlite_sidecars(path)
    path.write_bytes(b"good")
    sidecar = Path(str(path) + "-wal")
    with sidecar.open("wb") as output:
        output.truncate(64 * 1024 * 1024 + 1)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="budget"):
        capture_disconnected_sqlite_sidecars(path)


def test_unsupported_platform_fails_closed(tmp_path, monkeypatch):
    path = _db(tmp_path)
    monkeypatch.setattr(module.os, "supports_dir_fd", set())
    with pytest.raises(SQLiteSidecarCustodyRejected, match="unsupported"):
        capture_disconnected_sqlite_sidecars(path)
