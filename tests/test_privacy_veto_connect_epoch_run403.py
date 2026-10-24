"""A privacy veto source cannot switch while opening its SQLite handle.

These tests use only disposable offline fixtures; a local veto is not a
human-consent artifact, secure file descriptor, or personal-data erasure.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.personal_context_revocation_review as revocation
from ark.memory.contracts import MemoryScope


def _fixture(tmp_path: Path):
    path = tmp_path / "revocations.sqlite"
    ledger = revocation.SyntheticContextRevocationLedger(path)
    return ledger, path, MemoryScope("offline-owner", "private")


def _operation(ledger, scope, readonly):
    if readonly:
        ledger.assert_not_revoked((scope,))
    else:
        ledger.revoke(scope, at_ms=100)


def _count(path: Path):
    with sqlite3.connect(path) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations"
        ).fetchone()[0]


@pytest.mark.parametrize("readonly", (False, True))
@pytest.mark.parametrize("boundary", ("resolve", "as_uri"))
def test_path_callbacks_cannot_retarget_privacy_veto_source(
    tmp_path: Path, monkeypatch, readonly: bool, boundary: str,
):
    ledger, path, scope = _fixture(tmp_path)
    original = getattr(Path, boundary)
    invoked = []

    def retarget(current, *args, **kwargs):
        result = original(current, *args, **kwargs)
        invoked.append(boundary)
        ledger.path = Path(str(path))
        return result

    monkeypatch.setattr(Path, boundary, retarget)
    with pytest.raises(
        revocation.SyntheticContextRevocationRejected,
        match="source path changed",
    ):
        _operation(ledger, scope, readonly)
    assert invoked == [boundary]
    assert _count(path) == 0


@pytest.mark.parametrize("readonly", (False, True))
def test_connected_handle_is_closed_on_source_drift(
    tmp_path: Path, monkeypatch, readonly: bool,
):
    ledger, path, scope = _fixture(tmp_path)
    original_connect = sqlite3.connect
    opened = []

    def connecting(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        ledger.path = Path(str(path))
        return connection

    monkeypatch.setattr(revocation.sqlite3, "connect", connecting)
    with pytest.raises(
        revocation.SyntheticContextRevocationRejected,
        match="source path changed",
    ):
        _operation(ledger, scope, readonly)
    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        opened[0].execute("SELECT 1")
    with original_connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations"
        ).fetchone() == (0,)


def test_normal_privacy_veto_remains_restart_safe(tmp_path: Path):
    ledger, path, scope = _fixture(tmp_path)
    ledger.assert_not_revoked((scope,))
    digest = ledger.revoke(scope, at_ms=100)
    assert len(digest) == 64
    reopened = revocation.SyntheticContextRevocationLedger(path)
    with pytest.raises(
        revocation.SyntheticContextRevocationRejected, match="scope revoked",
    ):
        reopened.assert_not_revoked((scope,))
    assert _count(path) == 1
