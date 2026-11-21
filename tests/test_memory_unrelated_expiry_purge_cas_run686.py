"""A foreign expiry purge cannot invalidate a still-live Memory generation.

Two independent SQLite handles and a separately opened purger model local
concurrent storage. No content hash is writer identity, consent or permission.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("foreign_owner", "foreign_namespace"),
    (
        ("owner-b", "private"),
        ("owner-a", "notes"),
        ("owner-a", "private"),
    ),
)
@pytest.mark.parametrize("recreate_foreign", (False, True))
def test_foreign_expiry_and_recreation_do_not_stale_live_target(
    tmp_path, foreign_owner, foreign_namespace, recreate_foreign,
):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-a", "private")
    foreign_scope = MemoryScope(foreign_owner, foreign_namespace)
    target = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    foreign = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    purger = SQLiteMemoryStore(path, clock_ms=lambda: 200)

    original = target.put(
        MemoryWrite(scope, "retained-source", "private-data", expires_at_ms=1000),
    )
    retained = observe_memory_generation_for_cas(
        target, scope, "retained-source",
    )
    to_expire = foreign.put(
        MemoryWrite(
            foreign_scope, "foreign-source", "temporary-data",
            expires_at_ms=150,
        ),
    )
    assert purger.purge_expired(scope=foreign_scope) == 1

    if recreate_foreign:
        replacement = SQLiteMemoryStore(
            path, clock_ms=lambda: 200,
        ).put(
            MemoryWrite(foreign_scope, "foreign-source", "different-generation"),
            expected_revision=0,
        )
        assert replacement.memory_id == to_expire.memory_id
        assert replacement.content == "different-generation"
    else:
        assert foreign.get(to_expire.memory_id, foreign_scope) is None

    assert foreign.get(original.memory_id, scope).revision == 1
    result = generation_fenced_memory_update(
        target,
        MemoryWrite(
            scope, "retained-source", "new-private-data",
            expires_at_ms=900,
        ),
        retained=retained,
    )
    assert result.memory_id == original.memory_id
    assert result.revision == 2
    assert result.content == "new-private-data"
    assert result.expires_at_ms == 900
    assert purger.get(original.memory_id, scope) == result

    fresh = observe_memory_generation_for_cas(
        purger, scope, "retained-source",
    )
    assert fresh.create_event_id == retained.create_event_id
    assert fresh.last_event_id > retained.last_event_id
    assert fresh.external_action_authorized is False
    assert fresh.consent_authenticated is False
