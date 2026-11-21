"""Run949: independently retained privacy veto history rejects row replacement.

Synthetic local SQLite rows represent privacy-denial *fixtures* only.
A hash witness is not authenticated consent, real erasure or atomic custody.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("change", ("remove", "change_time", "replace_scope"))
def test_retained_privacy_veto_cannot_be_erased_or_rewritten_at_cold_restart(
    tmp_path, change: str,
) -> None:
    path = tmp_path / "retained-revocation.sqlite3"
    private = MemoryScope("synthetic-owner", "private")
    unrelated = MemoryScope("another-owner", "other")
    ledger = SyntheticContextRevocationLedger(path)
    ledger.revoke(private, at_ms=150)
    before = review_revocation_continuity(ledger)
    assert len(before.rows) == 1
    digest, when = before.rows[0]
    assert when == 150
    assert "synthetic-owner" not in repr(before)

    # Bypass the append-only fixture API deliberately to simulate rollback.
    with sqlite3.connect(path) as conn:
        if change == "change_time":
            conn.execute(
                "UPDATE synthetic_context_revocations "
                "SET revoked_at_ms=151 WHERE scope_digest=?", (digest,),
            )
        else:
            conn.execute(
                "DELETE FROM synthetic_context_revocations "
                "WHERE scope_digest=?", (digest,),
            )
    if change == "replace_scope":
        SyntheticContextRevocationLedger(
            path, require_existing=True,
        ).revoke(unrelated, at_ms=200)

    with pytest.raises(SyntheticContextRevocationRejected):
        review_revocation_continuity(
            SyntheticContextRevocationLedger(path, require_existing=True),
            retained=before,
        )
    # The offline reader neither silently restores the row nor certifies
    # a deletion as permissible. No external privacy authority is granted.
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest,revoked_at_ms "
            "FROM synthetic_context_revocations ORDER BY scope_digest",
        ).fetchall()
    assert rows != list(before.rows)


@pytest.mark.parametrize("other_first", (False, True))
def test_unrelated_new_veto_preserves_private_retained_prefix(
    tmp_path, other_first: bool,
) -> None:
    path = tmp_path / "append-revocation.sqlite3"
    private = MemoryScope("synthetic-owner", "private")
    other = MemoryScope("another-owner", "other")
    ledger = SyntheticContextRevocationLedger(path)
    first, second = (other, private) if other_first else (private, other)
    ledger.revoke(first, at_ms=100)
    retained = review_revocation_continuity(ledger)
    ledger.revoke(second, at_ms=120)
    fresh = review_revocation_continuity(
        SyntheticContextRevocationLedger(path, require_existing=True),
        retained=retained,
    )
    assert len(fresh.rows) == 2
    assert fresh.witness_id != retained.witness_id
    with pytest.raises(SyntheticContextRevocationRejected):
        SyntheticContextRevocationLedger(
            path, require_existing=True,
        ).assert_not_revoked((private,))
