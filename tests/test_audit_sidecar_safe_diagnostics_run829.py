"""Audit preflight classifies unsafe SQLite sidecars without leaking paths.

All sources are disposable; an aliased -wal/-shm/-journal is always rejected.
There is no retry, deletion, action execution or permission granting.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
@pytest.mark.parametrize("kind", ("directory", "symlink", "hardlink"))
def test_audit_refuses_aliased_sidecar_with_path_free_metadata(
    tmp_path: Path, suffix: str, kind: str,
) -> None:
    database = tmp_path / "audit-private-path.sqlite3"
    SQLiteActionAudit(database, clock_ms=lambda: 1000)
    foreign = tmp_path / "foreign-private-payload"
    foreign.write_bytes(b"PRIVATE_SENTINEL_DO_NOT_DISCLOSE")
    sidecar = database.with_name(database.name + suffix)
    if kind == "directory":
        sidecar.mkdir()
        expected_mode = stat.S_IFDIR
        links = sidecar.lstat().st_nlink
    elif kind == "symlink":
        try:
            sidecar.symlink_to(foreign)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"symlink fixture unsupported: {exc}")
        expected_mode = stat.S_IFLNK
        links = 1
    else:
        try:
            os.link(foreign, sidecar)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"hardlink fixture unsupported: {exc}")
        expected_mode = stat.S_IFREG
        links = 2
    with pytest.raises(ActionAuditSchemaError, match="sidecar alias refused") as err:
        SQLiteActionAudit(database, clock_ms=lambda: 1000)
    detail = str(err.value)
    assert f"suffix={suffix}" in detail
    assert f"file_type={expected_mode:#o}" in detail
    # Some filesystems use differing nlink values for directories. Record
    # exactly the observed value without making it a policy exception.
    assert f"link_count={links}" in detail
    assert str(tmp_path) not in detail
    assert "PRIVATE_SENTINEL" not in detail
    assert foreign.read_bytes() == b"PRIVATE_SENTINEL_DO_NOT_DISCLOSE"
    assert sidecar.exists() or sidecar.is_symlink()


def test_regular_audit_sqlite_untouched_by_path_free_diagnostic(tmp_path: Path) -> None:
    database = tmp_path / "audit.sqlite3"
    first = SQLiteActionAudit(database, clock_ms=lambda: 1000)
    second = SQLiteActionAudit(database, clock_ms=lambda: 1000)
    assert first.events(after_event_id=0, limit=10) == []
    assert second.events(after_event_id=0, limit=10) == []
