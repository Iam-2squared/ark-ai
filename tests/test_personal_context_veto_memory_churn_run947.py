"""Run947: synthetic privacy veto survives post-revocation Memory churn.

Separate SQLite stores are deliberately not an atomic erasure transaction.
These fixtures never authorize context disclosure or external access.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("churn", ("update", "delete", "append"))
@pytest.mark.parametrize("foreign_namespace", (False, True))
def test_retained_revocation_veto_survives_memory_churn_and_cold_restart(
    tmp_path, churn: str, foreign_namespace: bool,
) -> None:
    memory_path = tmp_path / "synthetic-memory.sqlite"
    veto_path = tmp_path / "synthetic-revocations.sqlite"
    scope = MemoryScope("private-owner", "secrets")
    foreign = (
        MemoryScope("private-owner", "unrelated")
        if foreign_namespace else MemoryScope("foreign-owner", "secrets")
    )
    writer = SQLiteMemoryStore(memory_path, clock_ms=lambda: 100)
    initial = writer.put(MemoryWrite(scope, "source-a", "PRIVATE_SENTINEL_1"))
    writer.put(MemoryWrite(foreign, "foreign-source", "FOREIGN_SENTINEL"))
    ledger = SyntheticContextRevocationLedger(veto_path)
    prior = review_revocation_continuity(ledger)
    ledger.revoke(scope, at_ms=150)

    after_veto_writer = SQLiteMemoryStore(memory_path, clock_ms=lambda: 200)
    if churn == "update":
        after_veto_writer.put(
            MemoryWrite(scope, "source-a", "PRIVATE_SENTINEL_2"),
            expected_revision=1,
        )
    elif churn == "delete":
        assert after_veto_writer.delete(
            initial.memory_id, scope, expected_revision=1,
        )
    else:
        after_veto_writer.put(
            MemoryWrite(scope, "source-b", "PRIVATE_SENTINEL_2"),
        )

    restarted_memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 250)
    restarted_veto = SyntheticContextRevocationLedger(
        veto_path, require_existing=True,
    )
    private = review_synthetic_retention_inventory(
        restarted_memory, scope, restarted_veto, now_ms=250,
        retained_revocations=prior,
    )
    assert private.revoked is True
    assert private.context_use_authorized is False
    assert private.deletion_authorized is False
    assert private.erasure_completed is False
    with pytest.raises(SyntheticContextRevocationRejected):
        restarted_veto.assert_not_revoked((scope,))

    unrelated = review_synthetic_retention_inventory(
        restarted_memory, foreign, restarted_veto, now_ms=250,
        retained_revocations=prior,
    )
    assert unrelated.revoked is False
    assert unrelated.scope_digest != private.scope_digest
    assert unrelated.context_use_authorized is False
    restarted_veto.assert_not_revoked((foreign,))
    for secret in ("PRIVATE_SENTINEL_1", "PRIVATE_SENTINEL_2", "FOREIGN_SENTINEL"):
        assert secret not in repr(private)
        assert secret not in repr(unrelated)
