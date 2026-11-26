"""SQLite sidecar path custody: synthetic temporary stores only.

No real private data, hardware, tools, candidate weights or external services.
The checks run before a SQLite connection is handed an aliased journal path.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _sidecar(path: Path, suffix: str) -> Path:
    return path.with_name(path.name + suffix)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_orphaned_regular_sidecar_blocks_bootstrap_without_creating_main(tmp_path, suffix):
    path = tmp_path / "memory.sqlite"
    sidecar = _sidecar(path, suffix)
    sidecar.write_bytes(b"previously retained synthetic journal")
    retained = sidecar.read_bytes()
    with pytest.raises(MemorySchemaError, match="orphaned"):
        SQLiteMemoryStore(path)
    assert not path.exists()
    assert sidecar.read_bytes() == retained


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_symlink_sidecar_rejected_before_bootstrap(tmp_path, suffix):
    path = tmp_path / "memory.sqlite"
    private = tmp_path / "synthetic-other-file"
    private.write_bytes(b"outside contents stay untouched")
    alias = _sidecar(path, suffix)
    try:
        alias.symlink_to(private)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this runner")
    with pytest.raises(MemorySchemaError, match="orphaned"):
        SQLiteMemoryStore(path)
    assert not path.exists()
    assert private.read_bytes() == b"outside contents stay untouched"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_hardlink_sidecar_rejected_before_existing_db_open(tmp_path, suffix):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 10)
    private = tmp_path / "outside"
    private.write_bytes(b"separate fixture")
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained an active journal; do not disturb it")
    os.link(private, alias)
    scope = MemoryScope("test-owner")
    with pytest.raises(MemorySchemaError, match="sidecar"):
        store.get("mem_" + "0" * 64, scope)
    with pytest.raises(MemorySchemaError, match="sidecar"):
        store.put(MemoryWrite(scope, "source", "secret fixture"))
    assert private.read_bytes() == b"separate fixture"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_directory_sidecar_rejected_on_existing_database(tmp_path, suffix):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained an active journal; do not disturb it")
    alias.mkdir()
    with pytest.raises(MemorySchemaError, match="sidecar"):
        store.get("mem_" + "0" * 64, MemoryScope("test-owner"))
    assert alias.is_dir()


@pytest.mark.skipif(os.name != "posix", reason="FIFOs are POSIX-only")
def test_fifo_sidecar_rejected_before_sqlite_read(tmp_path):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path)
    alias = _sidecar(path, "-wal")
    if alias.exists():
        pytest.skip("SQLite retained an active journal; do not disturb it")
    os.mkfifo(alias)
    with pytest.raises(MemorySchemaError, match="sidecar"):
        store.get("mem_" + "0" * 64, MemoryScope("test-owner"))


def test_regular_sqlite_sidecars_are_still_permitted_in_local_path_preflight(tmp_path):
    from ark.memory.sqlite_store import _require_safe_memory_path

    path = tmp_path / "memory.sqlite"
    SQLiteMemoryStore(path)
    for suffix in ("-wal", "-shm", "-journal"):
        alias = _sidecar(path, suffix)
        if not alias.exists():
            alias.write_bytes(b"synthetic regular sidecar metadata")
    _require_safe_memory_path(path, create=False)


def test_missing_main_still_uses_existing_read_error_contract(tmp_path):
    from ark.memory.sqlite_store import _require_safe_memory_path

    with pytest.raises(sqlite3.OperationalError, match="unavailable"):
        _require_safe_memory_path(tmp_path / "not-present.sqlite", create=False)
