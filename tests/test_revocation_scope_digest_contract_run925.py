"""Privacy veto rejects substituted scope validators before private digest work."""

from __future__ import annotations

import sqlite3

import pytest

import ark.personal_context_revocation_review as veto
from ark.memory.contracts import MemoryScope


@pytest.mark.parametrize(
    "mutation",
    ["post_init", "owner_slot", "namespace_slot", "sha256", "dumps", "scope_type"],
)
def test_changed_scope_digest_contract_does_not_append_veto(
    tmp_path, monkeypatch, mutation,
):
    path = tmp_path / "revocations.sqlite"
    ledger = veto.SyntheticContextRevocationLedger(path)
    scope = MemoryScope("private-owner", "private-notes")

    def should_not_run(*args, **kwargs):
        pytest.fail("unreviewed scope or digest callback executed")

    if mutation == "post_init":
        monkeypatch.setattr(MemoryScope, "__post_init__", should_not_run)
    elif mutation == "owner_slot":
        monkeypatch.setattr(MemoryScope, "owner_id", property(should_not_run))
    elif mutation == "namespace_slot":
        monkeypatch.setattr(MemoryScope, "namespace", property(should_not_run))
    elif mutation == "sha256":
        monkeypatch.setattr(veto.hashlib, "sha256", should_not_run)
    elif mutation == "dumps":
        monkeypatch.setattr(veto.json, "dumps", should_not_run)
    else:
        monkeypatch.setattr(veto, "MemoryScope", object)

    with pytest.raises(
        veto.SyntheticContextRevocationRejected,
        match="revocation scope digest implementation changed",
    ):
        ledger.revoke(scope, at_ms=100)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_context_revocations"
        ).fetchone() == (0,)


def test_original_private_scope_veto_survives_restart(tmp_path):
    path = tmp_path / "revocations.sqlite"
    scope = MemoryScope("private-owner", "private-notes")
    ledger = veto.SyntheticContextRevocationLedger(path)
    digest = ledger.revoke(scope, at_ms=100)
    assert len(digest) == 64
    restarted = veto.SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(veto.SyntheticContextRevocationRejected, match="revoked"):
        restarted.assert_not_revoked((scope,))
