"""Synthetic Personal Context vetoes remain deny-only across restarts.

This fixture does not erase content, authenticate human consent, prove external
clock time or provide atomic consistency with an independent Memory database.
"""

from __future__ import annotations

import pytest

from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def test_retained_veto_prefix_survives_restart_with_new_scope(tmp_path):
    path = tmp_path / "restart-veto.sqlite"
    original = SyntheticContextRevocationLedger(path)
    scope_a = MemoryScope("private-owner", "notes")
    scope_b = MemoryScope("private-owner", "history")
    original.revoke(scope_a, at_ms=100)
    retained = review_revocation_continuity(original)
    original.revoke(scope_b, at_ms=101)

    restarted = SyntheticContextRevocationLedger(path)
    advanced = review_revocation_continuity(restarted, retained=retained)
    assert len(retained.rows) == 1
    assert len(advanced.rows) == 2
    assert advanced.witness_id != retained.witness_id
    assert set(retained.rows).issubset(set(advanced.rows))
    for scope in (scope_a, scope_b):
        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            restarted.assert_not_revoked((scope,))
    assert "private-owner" not in repr(advanced)
    assert "notes" not in repr(advanced)
    assert "history" not in repr(advanced)


def test_second_sqlite_handle_cannot_revoke_same_scope_again(tmp_path):
    path = tmp_path / "two-handles-veto.sqlite"
    first = SyntheticContextRevocationLedger(path)
    second = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("synthetic-owner", "private")
    first.revoke(scope, at_ms=100)
    before = review_revocation_continuity(first)

    with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
        second.revoke(scope, at_ms=101)

    assert review_revocation_continuity(first, retained=before) == before
    assert review_revocation_continuity(second, retained=before) == before
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        second.assert_not_revoked((scope,))


def test_unrelated_scope_remains_separate_without_granting_consent(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "scoped-veto.sqlite")
    blocked = MemoryScope("owner-a", "notes")
    other_owner = MemoryScope("owner-b", "notes")
    other_namespace = MemoryScope("owner-a", "another")
    ledger.revoke(blocked, at_ms=100)
    assert ledger.assert_not_revoked((other_owner, other_namespace)) is None
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        ledger.assert_not_revoked((blocked, other_owner))
    assert len(review_revocation_continuity(ledger).rows) == 1
