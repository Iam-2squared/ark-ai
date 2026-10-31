"""Retention inventory pins revocation evidence before its earliest callback.

This fixture creates no privacy-use authority, disclosure, erasure or
authenticated retention decision.
"""

from pathlib import Path

import pytest

import ark.personal_context_retention_review as inventory
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_revocation_continuity_review import (
    SyntheticRevocationWitness,
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


@pytest.mark.parametrize(
    ("phase", "target"),
    (
        ("integrity", "equal_rows"),
        ("integrity", "memory_source"),
        ("integrity", "scope"),
        ("first_veto_read", "equal_rows"),
    ),
)
def test_retention_inventory_refuses_early_retained_rebase(
    tmp_path, monkeypatch, phase, target,
):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "local-privacy")
    memory.put(MemoryWrite(scope, "first", "synthetic sensitive fixture"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    ledger.revoke(MemoryScope("other-owner", "other-space"), at_ms=50)
    retained = review_revocation_continuity(ledger)
    original_rows = retained.rows
    original_path = memory.path
    original_namespace = scope.namespace
    assert original_rows
    calls = 0

    def drift():
        if target == "equal_rows":
            new_rows = tuple(list(original_rows))
            assert new_rows == original_rows and new_rows is not original_rows
            object.__setattr__(retained, "rows", new_rows)
        elif target == "memory_source":
            memory.path = Path(str(original_path))
        else:
            object.__setattr__(scope, "namespace", "different-space")

    if phase == "integrity":
        original = SyntheticRevocationWitness.assert_integrity

        def reflected_integrity(self):
            nonlocal calls
            original(self)
            if self is retained:
                calls += 1
                if calls == 1:
                    drift()

        monkeypatch.setattr(
            SyntheticRevocationWitness, "assert_integrity", reflected_integrity,
        )
    else:
        original = inventory.review_revocation_continuity

        def reflected_read(*args, **kwargs):
            nonlocal calls
            result = original(*args, **kwargs)
            calls += 1
            if calls == 1:
                drift()
            return result

        monkeypatch.setattr(
            inventory, "review_revocation_continuity", reflected_read,
        )

    with pytest.raises(inventory.SyntheticRetentionRejected, match="changed"):
        inventory.review_synthetic_retention_inventory(
            memory, scope, ledger, now_ms=100, retained_revocations=retained,
        )
    assert calls == 1

    monkeypatch.undo()
    object.__setattr__(retained, "rows", original_rows)
    memory.path = original_path
    object.__setattr__(scope, "namespace", original_namespace)
    result = inventory.review_synthetic_retention_inventory(
        memory, scope, ledger, now_ms=100, retained_revocations=retained,
    )
    assert len(result.items) == 1
    assert result.context_use_authorized is False
    assert result.deletion_authorized is False
