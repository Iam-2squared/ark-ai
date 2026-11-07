"""A synthetic privacy veto must not silently switch its SQLite source."""

from pathlib import Path

import pytest

import ark.personal_context_revocation_continuity_review as continuity
import ark.personal_context_revocation_review as veto_module
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _fixture(tmp_path: Path):
    source = tmp_path / "veto #1 %.sqlite"
    other = tmp_path / "alternate.sqlite"
    ledger = SyntheticContextRevocationLedger(source)
    SyntheticContextRevocationLedger(other)
    return ledger, source, other, MemoryScope("private-owner", "profile")


def _count(path: Path) -> int:
    import sqlite3

    with sqlite3.connect(path) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations"
        ).fetchone()[0]


@pytest.mark.parametrize("operation", ["write", "read", "continuity"])
def test_reflected_source_retarget_mid_review_denied_without_commit(
    tmp_path: Path, monkeypatch, operation: str,
):
    ledger, source, alternate, scope = _fixture(tmp_path)
    original = veto_module._validate

    def redirect(conn):
        original(conn)
        ledger.path = alternate

    if operation == "continuity":
        monkeypatch.setattr(continuity, "_validate", redirect)
    else:
        monkeypatch.setattr(veto_module, "_validate", redirect)
    with pytest.raises(SyntheticContextRevocationRejected, match="source path"):
        if operation == "write":
            ledger.revoke(scope, at_ms=100)
        elif operation == "read":
            ledger.assert_not_revoked((scope,))
        else:
            continuity.review_revocation_continuity(ledger)
    assert _count(source) == 0
    assert _count(alternate) == 0


@pytest.mark.parametrize("operation", ["write", "read", "continuity"])
def test_source_retarget_before_entry_is_rejected(
    tmp_path: Path, operation: str,
):
    ledger, source, alternate, scope = _fixture(tmp_path)
    ledger.path = alternate
    with pytest.raises(SyntheticContextRevocationRejected, match="source path"):
        if operation == "write":
            ledger.revoke(scope, at_ms=100)
        elif operation == "read":
            ledger.assert_not_revoked((scope,))
        else:
            continuity.review_revocation_continuity(ledger)
    assert _count(source) == _count(alternate) == 0


def test_normal_revocation_remains_restart_safe_and_deny_only(tmp_path: Path):
    ledger, path, _alternate, scope = _fixture(tmp_path)
    witness_before = continuity.review_revocation_continuity(ledger)
    digest = ledger.revoke(scope, at_ms=100)
    assert len(digest) == 64
    reopened = SyntheticContextRevocationLedger(path)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        reopened.assert_not_revoked((scope,))
    witness_after = continuity.review_revocation_continuity(
        reopened, retained=witness_before,
    )
    assert len(witness_after.rows) == 1
    assert witness_after != witness_before
