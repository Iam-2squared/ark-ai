"""A separately retained veto witness detects local privacy-ledger rollback.

Disposable synthetic scopes and SQLite only. These tests do not establish
authenticated user consent, independently trusted storage, or global erasure.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("tamper", ("delete", "timestamp", "digest"))
def test_retained_revocation_veto_refuses_valid_schema_rollback(
    tmp_path: Path, tamper: str,
) -> None:
    path = tmp_path / "privacy-veto.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("private-owner", "private")
    marker = ledger.revoke(scope, at_ms=100)
    witness = review_revocation_continuity(ledger)
    assert len(witness.rows) == 1

    # Malicious/local recovery can preserve SQLite schema and quick_check
    # while altering a veto row. The witness must be kept separately.
    with sqlite3.connect(path) as conn:
        if tamper == "delete":
            conn.execute(
                "DELETE FROM synthetic_context_revocations WHERE scope_digest=?",
                (marker,),
            )
        elif tamper == "timestamp":
            conn.execute(
                "UPDATE synthetic_context_revocations SET revoked_at_ms=? "
                "WHERE scope_digest=?",
                (101, marker),
            )
        else:
            conn.execute(
                "UPDATE synthetic_context_revocations SET scope_digest=? "
                "WHERE scope_digest=?",
                ("f" * 64, marker),
            )

    restarted = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected):
        review_revocation_continuity(restarted, retained=witness)


def test_new_veto_preserves_prior_retained_witness(tmp_path: Path) -> None:
    path = tmp_path / "privacy-veto.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    first_scope = MemoryScope("private-owner-a", "private")
    second_scope = MemoryScope("private-owner-b", "private")
    ledger.revoke(first_scope, at_ms=100)
    witness = review_revocation_continuity(ledger)
    ledger.revoke(second_scope, at_ms=110)

    restarted = SyntheticContextRevocationLedger(path, require_existing=True)
    next_witness = review_revocation_continuity(restarted, retained=witness)
    assert len(next_witness.rows) == 2
    assert next_witness.witness_id != witness.witness_id
    for scope in (first_scope, second_scope):
        with pytest.raises(SyntheticContextRevocationRejected):
            restarted.assert_not_revoked((scope,))
