"""Synthetic privacy-veto SQLite sidecars cannot bypass path custody.

All fixtures live in pytest temp directories. A rejection never opens the
aliased sidecar, retries SQLite, clears a veto, exports data or grants consent.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    genesis_privacy_veto_witness,
)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_directory_sidecar_rejected_before_existing_read(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "veto.sqlite"
    store = DisconnectedPrivacyVetoLedger(path)
    sidecar = path.with_name(path.name + suffix)
    sidecar.mkdir()
    with pytest.raises(OfflinePrivacyVetoRejected, match="sidecar alias"):
        store.witness()
    assert sidecar.is_dir()
    sidecar.rmdir()
    assert store.witness() == genesis_privacy_veto_witness()


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_hardlinked_sidecar_rejected_without_touching_other_file(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "veto.sqlite"
    DisconnectedPrivacyVetoLedger(path)
    original = tmp_path / "other-synthetic-file"
    original.write_bytes(b"unchanged sentinel")
    sidecar = path.with_name(path.name + suffix)
    try:
        os.link(original, sidecar)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"hardlinks unavailable: {exc}")
    with pytest.raises(OfflinePrivacyVetoRejected, match="sidecar alias"):
        DisconnectedPrivacyVetoLedger(path, require_existing=True)
    assert original.read_bytes() == b"unchanged sentinel"
    assert sidecar.samefile(original)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_orphaned_sidecar_refused_before_implicit_database_create(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "missing-veto.sqlite"
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"untrusted synthetic sidecar")
    with pytest.raises(OfflinePrivacyVetoRejected, match="orphaned"):
        DisconnectedPrivacyVetoLedger(path)
    assert not path.exists()
    assert sidecar.read_bytes() == b"untrusted synthetic sidecar"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_symbolic_sidecar_refused_before_existing_open(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "veto.sqlite"
    store = DisconnectedPrivacyVetoLedger(path)
    original = tmp_path / "synthetic-target"
    original.write_bytes(b"untouched")
    sidecar = path.with_name(path.name + suffix)
    try:
        sidecar.symlink_to(original)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    with pytest.raises(OfflinePrivacyVetoRejected, match="sidecar alias"):
        store.witness()
    assert original.read_bytes() == b"untouched"
    assert sidecar.is_symlink()


def test_single_regular_file_without_sidecars_remains_readable(tmp_path: Path) -> None:
    path = tmp_path / "veto.sqlite"
    store = DisconnectedPrivacyVetoLedger(path)
    assert store.witness() == genesis_privacy_veto_witness()
