"""Restart-safe synthetic revocation markers never imply fresh consent.

All fixtures are disposable local SQLite files and artificial scope names.
No real personal context is accessed, shared, restored or deleted.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def test_restarted_revocation_remains_a_veto_and_duplicate_is_not_regrant(tmp_path):
    path = tmp_path / "veto.sqlite"
    scope = MemoryScope("synthetic-owner", "profile")
    ledger = SyntheticContextRevocationLedger(path)
    digest = ledger.revoke(scope, at_ms=100)
    restarted = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        restarted.assert_not_revoked((scope,))
    with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
        restarted.revoke(scope, at_ms=101)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations",
        ).fetchall()
    assert rows == [(digest, 100)]


def test_clock_regression_on_second_scope_keeps_first_veto_intact(tmp_path):
    path = tmp_path / "veto.sqlite"
    first = MemoryScope("synthetic-owner", "profile")
    second = MemoryScope("synthetic-owner", "notes")
    ledger = SyntheticContextRevocationLedger(path)
    first_digest = ledger.revoke(first, at_ms=100)
    with pytest.raises(SyntheticContextRevocationRejected, match="clock regressed"):
        ledger.revoke(second, at_ms=99)
    ledger.assert_not_revoked((second,))
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        ledger.assert_not_revoked((first,))
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations",
        ).fetchall()
    assert rows == [(first_digest, 100)]


def test_missing_recovery_file_refuses_silent_empty_veto_bootstrap(tmp_path):
    path = tmp_path / "not-present.sqlite"
    assert not path.exists()
    with pytest.raises(SyntheticContextRevocationRejected, match="missing"):
        SyntheticContextRevocationLedger(path, require_existing=True)
    assert not path.exists()
