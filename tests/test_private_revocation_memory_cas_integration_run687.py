"""A scoped privacy veto survives independently committed Memory CAS events.

The revocation ledger is a separate SQLite source: a Memory update cannot
clear the veto, prove consent, or license private context disclosure.
All input content is synthetic and stays out of returned diagnostics.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.personal_context_retention_review import (
    RetentionState,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


@pytest.mark.parametrize(
    ("foreign_owner", "foreign_namespace"),
    (
        ("other-owner", "private"),
        ("owner-a", "tasks"),
        ("other-owner", "tasks"),
    ),
)
def test_revocation_remains_scoped_across_independent_cas_and_cold_readers(
    tmp_path, foreign_owner, foreign_namespace,
):
    path = tmp_path / "memory.sqlite"
    veto_path = tmp_path / "revocations.sqlite"
    scope = MemoryScope("owner-a", "private")
    unrelated = MemoryScope(foreign_owner, foreign_namespace)
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    ledger = SyntheticContextRevocationLedger(veto_path)

    private = first.put(MemoryWrite(
        scope, "source", "sensitive-before", expires_at_ms=300,
    ))
    other = second.put(MemoryWrite(
        unrelated, "source", "foreign-before", expires_at_ms=300,
    ))
    retained = observe_memory_generation_for_cas(first, scope, "source")
    updated = generation_fenced_memory_update(
        second,
        MemoryWrite(scope, "source", "sensitive-after", expires_at_ms=250),
        retained=retained,
    )
    assert updated.memory_id == private.memory_id
    assert updated.revision == 2

    # A privacy veto starts after the independent CAS has committed.
    previous_veto = review_revocation_continuity(ledger)
    ledger.revoke(scope, at_ms=120)
    veto = review_revocation_continuity(ledger, retained=previous_veto)
    blocked = review_synthetic_retention_inventory(
        first, scope, ledger, now_ms=130, retained_revocations=previous_veto,
    )
    assert blocked.revoked is True
    assert len(blocked.items) == 1
    assert blocked.items[0].memory_id == private.memory_id
    assert blocked.items[0].revision == 2
    assert blocked.items[0].state is RetentionState.NOT_EXPIRED

    # A disjoint writer advances the global Memory event log, but cannot
    # change the revoked scope's inventory or the independent veto chain.
    foreign_token = observe_memory_generation_for_cas(second, unrelated, "source")
    foreign_update = generation_fenced_memory_update(
        SQLiteMemoryStore(path, clock_ms=lambda: 130),
        MemoryWrite(unrelated, "source", "foreign-after", expires_at_ms=250),
        retained=foreign_token,
    )
    assert foreign_update.memory_id == other.memory_id
    assert foreign_update.revision == 2
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 130)
    reopened_veto = SyntheticContextRevocationLedger(veto_path)
    same = review_synthetic_retention_inventory(
        restarted, scope, reopened_veto,
        now_ms=130, retained_revocations=previous_veto,
    )
    foreign = review_synthetic_retention_inventory(
        restarted, unrelated, reopened_veto,
        now_ms=130, retained_revocations=previous_veto,
    )
    assert same == blocked
    assert foreign.revoked is False
    assert foreign.items[0].revision == 2
    assert review_revocation_continuity(
        reopened_veto, retained=previous_veto,
    ) == veto
    for report in (blocked, same, foreign):
        assert report.erasure_completed is False
        assert report.deletion_authorized is False
        assert report.context_use_authorized is False
        assert "sensitive-before" not in repr(report)
        assert "sensitive-after" not in repr(report)
        assert "foreign-before" not in repr(report)
        assert "foreign-after" not in repr(report)
