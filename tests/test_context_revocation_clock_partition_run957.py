"""Run957: cold local privacy veto never rolls back on clock rejection.

Only synthetic digest markers are persisted. An accepted marker is NOT proof
of consent, real personal-data erasure or authenticated clock provenance.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("invalid", (None, True, 3.5, -1, 2**63, "100"))
def test_rejected_revocation_clock_cannot_change_existing_private_veto(
    tmp_path, invalid: object,
) -> None:
    path = tmp_path / "synthetic-clock-revocation.sqlite"
    private = MemoryScope("synthetic-owner", "private")
    unrelated = MemoryScope("other-owner", "separate")
    ledger = SyntheticContextRevocationLedger(path)
    private_digest = ledger.revoke(private, at_ms=100)
    with sqlite3.connect(path) as conn:
        original = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
    with pytest.raises(
        SyntheticContextRevocationRejected, match="invalid revocation timestamp",
    ):
        ledger.revoke(unrelated, at_ms=invalid)  # type: ignore[arg-type]

    cold = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked((private,))
    cold.assert_not_revoked((unrelated,))
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall() == original == [(private_digest, 100)]


def test_cold_clock_regression_denies_second_scope_without_regrant(tmp_path) -> None:
    path = tmp_path / "synthetic-monotonic-revocation.sqlite"
    first = MemoryScope("synthetic-owner", "first-private")
    second = MemoryScope("synthetic-owner", "second-private")
    third = MemoryScope("other-owner", "separate")
    original = SyntheticContextRevocationLedger(path)
    first_digest = original.revoke(first, at_ms=100)
    cold = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="clock regressed"):
        cold.revoke(second, at_ms=99)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked((first,))
    cold.assert_not_revoked((second, third))

    # Equal timestamps can record independent vetoes without making either
    # older private scope usable again after a restart.
    second_digest = cold.revoke(second, at_ms=100)
    assert second_digest != first_digest
    again = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        again.assert_not_revoked((first, second, third))
    again.assert_not_revoked((third,))
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
    assert len(rows) == 2
    assert set(rows) == {(first_digest, 100), (second_digest, 100)}
    assert "synthetic-owner" not in repr(rows)
