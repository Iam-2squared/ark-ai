"""Run958: malformed persistent privacy veto is not silently reenrolled.

Local digest-only SQLite fixtures are NOT authenticated consent, personal
data deletion, or a cross-store snapshot. Deny instead of repairing tampering.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize(
    ("column", "corrupted"),
    (
        ("scope_digest", "g" * 64),
        ("scope_digest", "a" * 63),
        ("scope_digest", sqlite3.Binary(b"f" * 64)),
        ("revoked_at_ms", -1),
        ("revoked_at_ms", "not-an-integer"),
        ("revoked_at_ms", sqlite3.Binary(b"100")),
    ),
)
def test_cold_privacy_veto_corruption_denies_every_scope_without_repair(
    tmp_path, column: str, corrupted: object,
) -> None:
    path = tmp_path / "synthetic-veto-integrity.sqlite"
    private = MemoryScope("fixture-owner", "private")
    other = MemoryScope("unrelated-owner", "public")
    ledger = SyntheticContextRevocationLedger(path)
    digest = ledger.revoke(private, at_ms=100)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        ledger.assert_not_revoked((private,))
    ledger.assert_not_revoked((other,))

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT scope_digest FROM synthetic_context_revocations"
        ).fetchone() == (digest,)
        conn.execute(
            f"UPDATE synthetic_context_revocations SET {column}=?",
            (corrupted,),
        )
        tampered = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
        assert len(tampered) == 1

    with pytest.raises(SyntheticContextRevocationRejected):
        SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected):
        ledger.assert_not_revoked((private,))
    with pytest.raises(SyntheticContextRevocationRejected):
        ledger.assert_not_revoked((other,))
    with pytest.raises(SyntheticContextRevocationRejected):
        ledger.revoke(other, at_ms=101)

    # Invalid local evidence cannot be automatically rewritten or replaced
    # by a fresh empty ledger. A valid-file rollback needs separate custody.
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall() == tampered


def test_healthy_privacy_veto_remains_monotone_after_reopen(tmp_path) -> None:
    path = tmp_path / "healthy-veto.sqlite"
    private = MemoryScope("fixture-owner", "private")
    other = MemoryScope("other-owner", "private")
    first = SyntheticContextRevocationLedger(path)
    first.revoke(private, at_ms=100)
    cold = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked((private,))
    with pytest.raises(SyntheticContextRevocationRejected, match="clock regressed"):
        cold.revoke(other, at_ms=99)
    cold.revoke(other, at_ms=100)
    final = SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        final.assert_not_revoked((private, other))
