"""Synthetic WAL last-close transitions versus strict descriptor custody.

Only files in pytest's disposable tmp_path are inspected. SQLite closing a
normal final connection may unlink -shm; that behavior is not proof of an
attack and does NOT authorize accepting an unlinked held descriptor.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark import disconnected_sqlite_sidecar_custody as custody


def _supported() -> None:
    if (
        os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0)
        or not getattr(os, "O_DIRECTORY", 0)
        or os.open not in os.supports_dir_fd
        or os.stat not in os.supports_dir_fd
    ):
        pytest.skip("POSIX descriptor-relative sidecar proof only")


def _live_wal(tmp_path: Path) -> tuple[sqlite3.Connection, Path, Path]:
    path = tmp_path / "disposable.sqlite"
    connection = sqlite3.connect(path)
    if connection.execute("PRAGMA journal_mode=WAL").fetchone() != ("wal",):
        connection.close()
        pytest.skip("SQLite WAL unavailable")
    connection.execute("CREATE TABLE specimen(value INTEGER)")
    connection.execute("INSERT INTO specimen VALUES(1)")
    connection.commit()
    sidecar = Path(str(path) + "-shm")
    if not sidecar.exists():
        connection.close()
        pytest.skip("SQLite SHM unavailable")
    return connection, path, sidecar


def test_keeper_retains_named_wal_bundle_without_any_authority(tmp_path: Path) -> None:
    _supported()
    connection, path, _ = _live_wal(tmp_path)
    try:
        retained = custody.capture_disconnected_sqlite_sidecars(path)
        observed = custody.review_disconnected_sqlite_sidecars(path, retained)
        assert observed.fingerprint == retained.fingerprint
        assert observed.tool_execution_authorized is False
        assert observed.sqlite_transaction_atomicity_proven is False
        assert observed.independent_witness_custody_proven is False
    finally:
        connection.close()


def test_final_close_rejects_unlinked_held_shm_fd_and_stale_seal(
    tmp_path: Path,
) -> None:
    _supported()
    connection, path, shm = _live_wal(tmp_path)
    fd = os.open(shm, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        retained = custody.capture_disconnected_sqlite_sidecars(path)
        assert os.fstat(fd).st_nlink == 1
        connection.close()
        if os.fstat(fd).st_nlink != 0:
            pytest.skip("SQLite did not unlink held SHM on final close")
        with pytest.raises(
            custody.SQLiteSidecarCustodyRejected,
            match="singly linked regular file",
        ):
            custody._file_id(os.fstat(fd))
        with pytest.raises(
            custody.SQLiteSidecarCustodyRejected,
            match="custody differs|bundle changed",
        ):
            custody.review_disconnected_sqlite_sidecars(path, retained)
    finally:
        connection.close()
        os.close(fd)


def test_closing_keeper_between_two_scans_never_returns_clean_seal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _supported()
    connection, path, _ = _live_wal(tmp_path)
    original = custody._capture_once
    inspected = False

    def race(value: Path):
        nonlocal inspected
        first = original(value)
        if not inspected:
            inspected = True
            connection.close()
        return first

    try:
        with monkeypatch.context() as patch:
            patch.setattr(custody, "_capture_once", race)
            with pytest.raises(
                custody.SQLiteSidecarCustodyRejected,
                match="bundle changed",
            ):
                custody.capture_disconnected_sqlite_sidecars(path)
        assert inspected
    finally:
        connection.close()


@pytest.mark.parametrize("alias", ("symlink", "hardlink"))
def test_disconnected_sidecar_alias_is_refused_without_sqlite_connection(
    tmp_path: Path, alias: str,
) -> None:
    _supported()
    path = tmp_path / "synthetic.sqlite"
    path.write_bytes(b"offline metadata only")
    payload = tmp_path / "foreign-sidecar"
    payload.write_bytes(b"no private records")
    sidecar = Path(str(path) + "-shm")
    if alias == "symlink":
        sidecar.symlink_to(payload)
    else:
        os.link(payload, sidecar)
    with pytest.raises(custody.SQLiteSidecarCustodyRejected):
        custody.capture_disconnected_sqlite_sidecars(path)
