"""Privacy-safe, disconnected Personal Context SQLite sidecar custody.

All files are synthetic temporary paths. No source content is disclosed,
retention changed, replay authorized, or actual action dispatched.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
    genesis_offline_context_replay_witness,
)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_new_context_ledger_refuses_orphan_sidecar(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "context.sqlite"
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"orphaned synthetic sidecar")
    with pytest.raises(OfflineContextReplayRejected, match="sidecar"):
        DisconnectedContextReplayLedger(path, create=True)
    assert not path.exists()
    assert sidecar.read_bytes() == b"orphaned synthetic sidecar"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_existing_context_ledger_refuses_symlinked_sidecar(
    tmp_path: Path, suffix: str,
) -> None:
    path = tmp_path / "context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    baseline = ledger.witness()
    sidecar = path.with_name(path.name + suffix)
    try:
        sidecar.symlink_to(tmp_path / "private-not-a-sqlite-sidecar")
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links unavailable")
    with pytest.raises(OfflineContextReplayRejected, match="sidecar"):
        ledger.witness()
    with pytest.raises(OfflineContextReplayRejected, match="sidecar"):
        DisconnectedContextReplayLedger(path)
    assert path.exists()
    sidecar.unlink()
    assert ledger.witness() == baseline


def test_existing_context_ledger_refuses_hardlinked_sidecar(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    original = tmp_path / "source-bytes"
    original.write_bytes(b"synthetic private sidecar decoy")
    sidecar = path.with_name(path.name + "-shm")
    try:
        os.link(original, sidecar)
    except OSError:
        pytest.skip("hard links unavailable")
    with pytest.raises(OfflineContextReplayRejected, match="sidecar"):
        ledger.witness()
    assert original.read_bytes() == b"synthetic private sidecar decoy"


def test_unchanged_context_genesis_and_reopen_remain_readonly(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context.sqlite"
    ledger = DisconnectedContextReplayLedger(path, create=True)
    expected = genesis_offline_context_replay_witness()
    assert ledger.witness() == expected
    reopened = DisconnectedContextReplayLedger(path)
    assert reopened.witness() == expected
    assert expected.independent_custody_proven is False
