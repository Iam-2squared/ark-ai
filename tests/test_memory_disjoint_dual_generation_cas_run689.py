"""Two independently retained Memory generations can advance without aliasing.

Interleaved opt-in CAS updates share one SQLite event log but each token is
bound to its own identity and event prefix. A stale token is rejected after
its own update, regardless of writes in another owner/namespace/source.
Content stays local to synthetic fixtures; no consent or dispatch is inferred.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("second_owner", "second_namespace"),
    (
        ("owner-a", "private"),
        ("owner-a", "other"),
        ("owner-b", "private"),
    ),
)
@pytest.mark.parametrize("reverse_order", (False, True))
def test_separately_retained_cas_tokens_survive_interleaved_foreign_writes(
    tmp_path, second_owner, second_namespace, reverse_order,
):
    path = tmp_path / "memory.sqlite"
    a = MemoryScope("owner-a", "private")
    b = MemoryScope(second_owner, second_namespace)
    one = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    two = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row_a = one.put(MemoryWrite(a, "source-a", "before-a"))
    row_b = two.put(MemoryWrite(b, "source-b", "before-b"))
    token_a = observe_memory_generation_for_cas(one, a, "source-a")
    token_b = observe_memory_generation_for_cas(two, b, "source-b")
    assert row_a.memory_id != row_b.memory_id

    entries = (
        (one, a, "source-a", "after-a", token_a),
        (two, b, "source-b", "after-b", token_b),
    )
    for store, scope, source, content, token in (
        entries[::-1] if reverse_order else entries
    ):
        updated = generation_fenced_memory_update(
            store, MemoryWrite(scope, source, content), retained=token,
        )
        assert updated.revision == 2
        assert updated.content == content

    for store, scope, source, content, token in entries:
        cold = SQLiteMemoryStore(path, clock_ms=lambda: 100)
        record = cold.get(
            row_a.memory_id if source == "source-a" else row_b.memory_id, scope,
        )
        assert record.content == content
        assert record.revision == 2
        fresh = observe_memory_generation_for_cas(cold, scope, source)
        assert fresh.create_event_id == token.create_event_id
        assert fresh.last_event_id > token.last_event_id
        assert fresh.event_prefix_sha256 != token.event_prefix_sha256
        assert fresh.external_action_authorized is False
        assert fresh.consent_authenticated is False
        with pytest.raises(MemoryConflictError, match="generation changed"):
            generation_fenced_memory_update(
                store, MemoryWrite(scope, source, "stale-overwrite"),
                retained=token,
            )
        assert cold.get(record.memory_id, scope).content == content

    same_scope = a == b
    assert len(tuple(one.events(a))) == (4 if same_scope else 2)
    if not same_scope:
        assert len(tuple(two.events(b))) == 2
