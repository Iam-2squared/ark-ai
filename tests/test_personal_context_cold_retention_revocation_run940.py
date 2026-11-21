"""Cold restart preserves a synthetic privacy veto in retention review.

A per-scope local revocation is a negative-use witness, not evidence of
consent, completed erasure, independent custody or cross-store atomicity.
No actual personal information or external connector is accessed.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("foreign_namespace", (False, True))
def test_cold_retention_review_fences_exact_revoked_scope(
    tmp_path, foreign_namespace: bool,
) -> None:
    memory_path = tmp_path / "synthetic-memory.sqlite"
    veto_path = tmp_path / "synthetic-veto.sqlite"
    owner = MemoryScope("offline-owner", "private")
    other = (
        MemoryScope("offline-owner", "unrelated")
        if foreign_namespace else MemoryScope("offline-other", "private")
    )
    writer = SQLiteMemoryStore(memory_path, clock_ms=lambda: 100)
    first = writer.put(MemoryWrite(
        owner, "synthetic-first", "SYNTHETIC_PRIVATE_CONTENT",
        expires_at_ms=150,
    ))
    second = writer.put(MemoryWrite(
        other, "synthetic-second", "SYNTHETIC_FOREIGN_CONTENT",
    ))
    veto = SyntheticContextRevocationLedger(veto_path)
    genesis = review_revocation_continuity(veto)
    before = review_synthetic_retention_inventory(
        writer, owner, veto, now_ms=150, retained_revocations=genesis,
    )
    assert before.revoked is False
    assert [(item.memory_id, item.state) for item in before.items] == [
        (first.memory_id, RetentionState.EXPIRED),
    ]
    veto.revoke(owner, at_ms=140)
    cold_memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 150)
    cold_veto = SyntheticContextRevocationLedger(
        veto_path, require_existing=True,
    )
    after = review_synthetic_retention_inventory(
        cold_memory, owner, cold_veto, now_ms=150,
        retained_revocations=genesis,
    )
    assert after.revoked is True
    assert after.scope_digest == before.scope_digest
    assert after.inventory_digest != before.inventory_digest
    assert after.items == before.items
    assert after.expired_count == 1
    assert after.context_use_authorized is False
    assert after.deletion_authorized is False
    assert after.erasure_completed is False
    with pytest.raises(SyntheticContextRevocationRejected):
        cold_veto.assert_not_revoked((owner,))

    unrelated = review_synthetic_retention_inventory(
        cold_memory, other, cold_veto, now_ms=150,
        retained_revocations=genesis,
    )
    assert unrelated.revoked is False
    assert unrelated.scope_digest != after.scope_digest
    assert [(item.memory_id, item.state) for item in unrelated.items] == [
        (second.memory_id, RetentionState.NO_EXPIRY),
    ]
    assert unrelated.context_use_authorized is False
    assert unrelated.deletion_authorized is False
    cold_veto.assert_not_revoked((other,))
    assert "SYNTHETIC_PRIVATE_CONTENT" not in repr(after)
    assert "SYNTHETIC_FOREIGN_CONTENT" not in repr(unrelated)
