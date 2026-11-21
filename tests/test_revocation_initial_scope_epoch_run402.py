"""The initial revocation digest cannot redefine the intended Memory scope.

Local SQLite fixtures model a privacy veto, not verified human consent or
real erasure. No external personal-data connection is made.
"""

import sqlite3

import pytest

import ark.personal_context_revocation_review as revocation
from ark.memory.contracts import MemoryScope


@pytest.mark.parametrize(
    "field,decoy",
    (("owner_id", "wrong-owner"), ("namespace", "wrong-namespace")),
)
def test_first_digest_retarget_fails_without_writing_wrong_veto(
    tmp_path, monkeypatch, field, decoy,
):
    ledger = revocation.SyntheticContextRevocationLedger(
        tmp_path / "revocations.sqlite",
    )
    scope = MemoryScope("fixture-owner", "private")
    original_digest = revocation._scope_digest
    called = 0

    def retarget_first(argument):
        nonlocal called
        called += 1
        if called == 1:
            object.__setattr__(argument, field, decoy)
        return original_digest(argument)

    monkeypatch.setattr(revocation, "_scope_digest", retarget_first)
    with pytest.raises(
        revocation.SyntheticContextRevocationRejected,
        match="scope changed during revocation",
    ):
        ledger.revoke(scope, at_ms=42)
    assert called == 1
    with sqlite3.connect(ledger.path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations"
        ).fetchone() == (0,)


def test_unmodified_revocation_persists_exact_veto_only(tmp_path):
    ledger = revocation.SyntheticContextRevocationLedger(
        tmp_path / "revocations.sqlite",
    )
    scope = MemoryScope("fixture-owner", "private")
    digest = ledger.revoke(scope, at_ms=42)
    assert len(digest) == 64
    with pytest.raises(
        revocation.SyntheticContextRevocationRejected,
        match="context scope revoked",
    ):
        ledger.assert_not_revoked((MemoryScope("fixture-owner", "private"),))
    ledger.assert_not_revoked((MemoryScope("fixture-owner", "other"),))
