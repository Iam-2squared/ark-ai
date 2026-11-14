"""Disconnected occurrence and audit-link SQLite sidecar custody fixtures.

No actual permissions, tokens, ToolBackend execution or personal data.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
    _require_safe_occurrence_path,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticAuditLinkRejected,
    SyntheticOccurrenceAuditLinkStore,
    _require_safe_link_path,
)


@pytest.fixture(params=("occurrence", "audit-link"))
def ledger(request):
    if request.param == "occurrence":
        return SyntheticOccurrenceStore, _require_safe_occurrence_path, SyntheticReplayRejected
    return SyntheticOccurrenceAuditLinkStore, _require_safe_link_path, SyntheticAuditLinkRejected


def _sidecar(path: Path, suffix: str) -> Path:
    return path.with_name(path.name + suffix)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_orphan_sidecar_blocks_initial_store_creation(tmp_path, ledger, suffix):
    store_class, check, rejection = ledger
    path = tmp_path / "fixture.sqlite"
    orphan = _sidecar(path, suffix)
    orphan.write_bytes(b"unverified previous synthetic journal")
    preserved = orphan.read_bytes()
    with pytest.raises(rejection, match="orphaned"):
        store_class(path)
    assert not path.exists()
    assert orphan.read_bytes() == preserved
    with pytest.raises(sqlite3.OperationalError, match="missing"):
        check(path, create=False)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_existing_store_rejects_symlinked_sidecar_without_touching_target(
    tmp_path, ledger, suffix,
):
    store_class, check, rejection = ledger
    path = tmp_path / "fixture.sqlite"
    store_class(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained an active journal; leave it untouched")
    protected = tmp_path / "unrelated"
    protected.write_bytes(b"synthetic private sentinel")
    try:
        alias.symlink_to(protected)
    except (OSError, NotImplementedError):
        pytest.skip("runner cannot create filesystem symlinks")
    with pytest.raises(rejection, match="sidecar"):
        check(path, create=False)
    assert protected.read_bytes() == b"synthetic private sentinel"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_existing_store_rejects_hardlinked_sidecar(tmp_path, ledger, suffix):
    store_class, check, rejection = ledger
    path = tmp_path / "fixture.sqlite"
    store_class(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained an active journal; leave it untouched")
    protected = tmp_path / "unrelated"
    protected.write_bytes(b"synthetic private sentinel")
    os.link(protected, alias)
    with pytest.raises(rejection, match="sidecar"):
        check(path, create=False)
    assert protected.read_bytes() == b"synthetic private sentinel"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_existing_store_rejects_directory_sidecar(tmp_path, ledger, suffix):
    store_class, check, rejection = ledger
    path = tmp_path / "fixture.sqlite"
    store_class(path)
    alias = _sidecar(path, suffix)
    if alias.exists():
        pytest.skip("SQLite retained an active journal; leave it untouched")
    alias.mkdir()
    with pytest.raises(rejection, match="sidecar"):
        check(path, create=False)
    assert alias.is_dir()


@pytest.mark.skipif(os.name != "posix", reason="FIFO type requires POSIX")
def test_existing_store_rejects_fifo_sidecar(tmp_path, ledger):
    store_class, check, rejection = ledger
    path = tmp_path / "fixture.sqlite"
    store_class(path)
    alias = _sidecar(path, "-journal")
    if alias.exists():
        pytest.skip("SQLite retained an active journal; leave it untouched")
    os.mkfifo(alias)
    with pytest.raises(rejection, match="sidecar"):
        check(path, create=False)


def test_regular_sidecars_and_missing_sidecars_remain_accepted_in_path_preflight(
    tmp_path, ledger,
):
    store_class, check, _ = ledger
    path = tmp_path / "fixture.sqlite"
    store_class(path)
    check(path, create=False)
    for suffix in ("-wal", "-shm", "-journal"):
        alias = _sidecar(path, suffix)
        if not alias.exists():
            alias.write_bytes(b"synthetic regular metadata")
    check(path, create=False)
