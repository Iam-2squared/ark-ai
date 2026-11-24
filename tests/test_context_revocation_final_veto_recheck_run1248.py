"""Run1248: a veto appended during final history replay must stop projection return.

Only synthetic local SQLite fixtures are used. The final veto check narrows a
local race; it is not an atomic authorization lease for later consumption.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark import personal_context_revocation_continuity_review as continuity
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def test_revocation_appended_during_final_history_review_vetoes_projection(
    tmp_path, monkeypatch,
):
    memory = SQLiteMemoryStore(
        tmp_path / "synthetic-memory.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("fixture-owner", "private")
    memory.put(MemoryWrite(scope, "note", "SYNTHETIC-PRIVATE-CONTENT"))
    ledger = SyntheticContextRevocationLedger(
        tmp_path / "synthetic-revocations.sqlite",
    )
    request = CoherentSnapshotRequest(
        owner_id=scope.owner_id,
        namespaces=(scope.namespace,),
        per_namespace_limit=10,
    )
    policy = ContextSelectionPolicy(total_limit=10, per_namespace_limit=10)
    original = continuity.review_revocation_continuity
    calls = []

    def append_veto_after_final_history_read(source, *, retained=None):
        witness = original(source, retained=retained)
        calls.append(retained)
        if len(calls) == 2:
            # Simulate a concurrent local revocation after the final retained
            # history read but before the projection would be returned.
            source.revoke(scope, at_ms=200)
        return witness

    monkeypatch.setattr(
        continuity, "review_revocation_continuity",
        append_veto_after_final_history_read,
    )
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(memory, request, policy, ledger)

    assert len(calls) == 2
    with sqlite3.connect(ledger.path) as conn:
        rows = conn.execute(
            "SELECT scope_digest, revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][1] == 200
    assert "fixture-owner" not in repr(rows)
    assert "SYNTHETIC-PRIVATE-CONTENT" not in repr(rows)
