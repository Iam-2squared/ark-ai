"""Disconnected revocation must fail closed at both sides of SQLite COMMIT.

Only synthetic owner/scope values and temporary local SQLite are used.
A failed caller response after a commit is UNKNOWN, not consent or an
instruction to retry a privacy-sensitive operation.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    _scope_digest,
)


class _CommitFault:
    def __init__(self, wrapped: sqlite3.Connection, *, phase: str):
        self.wrapped = wrapped
        self.phase = phase

    def __getattr__(self, name: str):
        return getattr(self.wrapped, name)

    def commit(self) -> None:
        if self.phase == "before_commit":
            raise OSError("simulated failure before revocation COMMIT")
        self.wrapped.commit()
        raise OSError("simulated acknowledgement loss after revocation COMMIT")


@pytest.mark.parametrize(
    ("phase", "expected_rows"),
    (("before_commit", 0), ("after_commit", 1)),
)
def test_revocation_ambiguous_commit_keeps_durable_state_fail_closed(
    tmp_path: Path, monkeypatch, phase: str, expected_rows: int,
) -> None:
    path = tmp_path / "synthetic-revocations.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("synthetic-owner", "private")
    original_open = ledger._connect

    def connect_with_fault(*, readonly: bool):
        return _CommitFault(original_open(readonly=readonly), phase=phase)

    monkeypatch.setattr(ledger, "_connect", connect_with_fault)
    with pytest.raises(OSError, match="simulated .* revocation COMMIT"):
        ledger.revoke(scope, at_ms=501)

    # Fresh process-equivalent object, read-only SQLite witness, no synthetic
    # request-path callback or caller response trusted after the fault.
    recovered = SyntheticContextRevocationLedger(path, require_existing=True)
    with closing(sqlite3.connect(path)) as conn:
        rows = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
    assert len(rows) == expected_rows
    if phase == "after_commit":
        assert rows == [(_scope_digest(scope), 501)]
        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            recovered.assert_not_revoked((scope,))
        with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
            recovered.revoke(scope, at_ms=502)
    else:
        assert rows == []
        # Absence of a local veto is not independently authenticated consent.
        recovered.assert_not_revoked((scope,))


def test_unmodified_revocation_stays_denial_only_after_restart(tmp_path: Path) -> None:
    path = tmp_path / "synthetic-revocations.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    ledger = SyntheticContextRevocationLedger(path)
    assert ledger.revoke(scope, at_ms=0) == _scope_digest(scope)
    reopened = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        reopened.assert_not_revoked((scope,))
