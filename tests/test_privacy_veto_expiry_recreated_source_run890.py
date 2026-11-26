"""Privacy veto outlives Memory expiry, deletion, and source-id reuse.

All records are synthetic local SQLite data. A clean Memory namespace or fresh
revision is not a privacy consent grant, and neither DB is a cross-store lock.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def test_revoked_namespace_stays_blocked_through_expiry_and_source_recreation(
    tmp_path,
):
    now = [100]
    memory_path = tmp_path / "memory.sqlite"
    veto_path = tmp_path / "revocations.sqlite"
    store = SQLiteMemoryStore(memory_path, clock_ms=lambda: now[0])
    private = MemoryScope("synthetic-owner", "private")
    unrelated = MemoryScope("synthetic-owner", "notes")
    first = store.put(MemoryWrite(
        private, "stable-source", "old private fixture", expires_at_ms=150,
    ))
    store.put(MemoryWrite(
        unrelated, "separate-source", "unrelated fixture", expires_at_ms=400,
    ))
    ledger = SyntheticContextRevocationLedger(veto_path)
    ledger.revoke(private, at_ms=120)
    retained = review_revocation_continuity(ledger)

    now[0] = 200
    assert store.get(first.memory_id, private) is None
    assert store.purge_expired(scope=private, limit=1) == 1
    assert store.get(first.memory_id, private, include_expired=True) is None
    replacement = store.put(MemoryWrite(
        private, "stable-source", "new private fixture",
    ), expected_revision=0)
    assert replacement.memory_id == first.memory_id
    assert replacement.revision == 1

    reopened_store = SQLiteMemoryStore(memory_path, clock_ms=lambda: now[0])
    reopened_veto = SyntheticContextRevocationLedger(
        veto_path, require_existing=True,
    )
    assert review_revocation_continuity(reopened_veto, retained=retained) == retained
    policy = ContextSelectionPolicy(4, 4)
    private_request = CoherentSnapshotRequest("synthetic-owner", ("private",))
    mixed_request = CoherentSnapshotRequest(
        "synthetic-owner", ("notes", "private"),
    )
    for request in (private_request, mixed_request):
        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            review_fresh_nonrevoked_context(
                reopened_store, request, policy, reopened_veto,
                retained_revocations=retained,
            )

    notes = review_fresh_nonrevoked_context(
        reopened_store,
        CoherentSnapshotRequest("synthetic-owner", ("notes",)),
        policy,
        reopened_veto,
        retained_revocations=retained,
    )
    assert len(notes.items) == 1
    assert notes.items[0].content == "unrelated fixture"
    assert notes.action_authorized is False
    assert notes.dispatch_authorized is False
    assert "new private fixture" not in repr(notes)
