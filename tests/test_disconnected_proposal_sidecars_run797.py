"""Pure-local SQLite sidecar denial tests for synthetic proposal receipts."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_proposal_store as store

_PROPOSAL = "proposal_" + "c" * 64
_SIDECARS = ("-wal", "-shm", "-journal")


@pytest.mark.parametrize("suffix", _SIDECARS)
def test_sidecar_directory_rejected_before_read_and_write(tmp_path, suffix):
    path = tmp_path / "proposal.sqlite3"
    genesis = store.create_disconnected_proposal_store(path)
    sidecar = path.with_name(path.name + suffix)
    sidecar.mkdir()
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sidecar"):
        store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL)
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sidecar"):
        store.append_disconnected_proposal_transition(
            path, proposal_id=_PROPOSAL, new_state="PROPOSED",
            expected_revision=0, expected_tip=None, retained=genesis,
        )
    sidecar.rmdir()
    assert store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL).witness == genesis


@pytest.mark.parametrize("suffix", _SIDECARS)
def test_existing_sidecar_rejects_create_without_clobber(tmp_path, suffix):
    path = tmp_path / "proposal.sqlite3"
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"untrusted-old-sidecar")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sidecar"):
        store.create_disconnected_proposal_store(path)
    assert not path.exists()
    assert sidecar.read_bytes() == b"untrusted-old-sidecar"


@pytest.mark.parametrize("suffix", _SIDECARS)
def test_hardlinked_sidecar_rejected(tmp_path, suffix):
    path = tmp_path / "proposal.sqlite3"
    store.create_disconnected_proposal_store(path)
    other = tmp_path / "other.bin"
    other.write_bytes(b"never-overwrite")
    sidecar = path.with_name(path.name + suffix)
    try:
        sidecar.hardlink_to(other)
    except OSError:
        pytest.skip("filesystem cannot create hardlinks")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sidecar"):
        store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL)
    assert other.read_bytes() == b"never-overwrite"


@pytest.mark.parametrize("suffix", _SIDECARS)
def test_symlinked_sidecar_rejected_even_when_dangling(tmp_path, suffix):
    path = tmp_path / "proposal.sqlite3"
    store.create_disconnected_proposal_store(path)
    sidecar = path.with_name(path.name + suffix)
    try:
        sidecar.symlink_to(tmp_path / "missing-target")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this runner")
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sidecar"):
        store.inspect_disconnected_proposal_store(path, proposal_id=_PROPOSAL)


def test_regular_single_link_sidecars_allowed_for_existing_store(tmp_path):
    path = tmp_path / "proposal.sqlite3"
    store.create_disconnected_proposal_store(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (1,)
    sidecar = path.with_name(path.name + "-journal")
    sidecar.write_bytes(b"")
    # File metadata validation must not reject legitimate regular sidecars.
    store._sidecar_integrity(path, create=False)
    with pytest.raises(store.DisconnectedProposalStoreRejected, match="sidecar"):
        store._sidecar_integrity(path, create=True)
