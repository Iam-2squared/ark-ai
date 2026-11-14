"""Revocation veto persists when a source ID is revived after erasure/expiry.

All operations use offline SQLite fixtures. A local tombstone does not certify
global erasure, user consent or permission to use the replacement content.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_retention_review import (
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


@pytest.mark.parametrize(
    "intervention",
    ("manual_delete_recreate", "expiry_purge_recreate", "append_same_scope"),
)
def test_privacy_veto_survives_new_memory_lifetime_after_reopen(
    tmp_path, intervention,
):
    path = tmp_path / "memory.sqlite"
    revocations_path = tmp_path / "revocations.sqlite"
    scope = MemoryScope("owner-a", "private")
    memory = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    ledger = SyntheticContextRevocationLedger(revocations_path)
    original = memory.put(MemoryWrite(
        scope, "source", "sensitive original", expires_at_ms=150,
    ))
    ledger.revoke(scope, at_ms=110)
    retained = review_revocation_continuity(ledger)
    before = review_synthetic_retention_inventory(
        memory, scope, ledger, now_ms=100, retained_revocations=retained,
    )
    assert before.revoked is True
    assert len(before.items) == 1

    if intervention == "manual_delete_recreate":
        assert memory.delete(
            original.memory_id, scope, expected_revision=1,
        )
        replacement = writer.put(
            MemoryWrite(scope, "source", "new private generation"),
            expected_revision=0,
        )
        assert replacement.memory_id == original.memory_id
    elif intervention == "expiry_purge_recreate":
        assert writer.purge_expired(scope=scope) == 1
        replacement = writer.put(
            MemoryWrite(scope, "source", "new private generation"),
            expected_revision=0,
        )
        assert replacement.memory_id == original.memory_id
    else:
        replacement = writer.put(
            MemoryWrite(scope, "new-source", "another private value"),
        )
        assert replacement.memory_id != original.memory_id

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    reopened_ledger = SyntheticContextRevocationLedger(revocations_path)
    after = review_synthetic_retention_inventory(
        reopened, scope, reopened_ledger, now_ms=200,
        retained_revocations=retained,
    )
    assert after.revoked is True
    assert any(item.memory_id == replacement.memory_id for item in after.items)
    assert after.inventory_digest != before.inventory_digest
    assert review_revocation_continuity(
        reopened_ledger, retained=retained,
    ) == retained
    for report in (before, after):
        assert report.context_use_authorized is False
        assert report.deletion_authorized is False
        assert report.erasure_completed is False
        assert "sensitive original" not in repr(report)
        assert "new private generation" not in repr(report)
        assert "another private value" not in repr(report)
