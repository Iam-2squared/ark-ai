"""Generation-fenced Memory CAS never extends retention or revives expired rows.

Synthetic local SQLite clocks are NOT trusted wall clocks or consent evidence.
A failed CAS must not append an update event or silently retry.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _state(tmp_path):
    clock = [1000]
    path = tmp_path / "generation-expiry.sqlite"
    writer = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    reviewer = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    scope = MemoryScope("local-only", "notes")
    original = writer.put(
        MemoryWrite(scope, "fixture-source", "before", expires_at_ms=2000)
    )
    retained = observe_memory_generation_for_cas(reviewer, scope, "fixture-source")
    return clock, writer, reviewer, scope, original, retained


@pytest.mark.parametrize(
    ("now_ms", "new_expiry", "error_type", "message"),
    (
        (1100, 2001, MemoryGenerationCASRejected, "expiry extension"),
        (1100, None, MemoryGenerationCASRejected, "expiry extension"),
        (1100, 1100, MemoryGenerationCASRejected, "proposed expiry"),
        (2000, 2100, MemoryConflictError, "source expired"),
        (999, 1900, MemoryConflictError, "clock regressed"),
    ),
)
def test_generation_cas_denies_retention_relaxation_expiry_and_clock_rollback(
    tmp_path, now_ms, new_expiry, error_type, message,
):
    clock, writer, reviewer, scope, original, retained = _state(tmp_path)
    prior = writer.events(scope)
    row_before = writer.get(original.memory_id, scope, include_expired=True)
    clock[0] = now_ms

    with pytest.raises(error_type, match=message):
        generation_fenced_memory_update(
            reviewer,
            MemoryWrite(scope, "fixture-source", "after", expires_at_ms=new_expiry),
            retained=retained,
        )

    assert writer.events(scope) == prior
    assert reviewer.get(original.memory_id, scope, include_expired=True) == row_before
    assert retained.consent_authenticated is False
    assert retained.external_action_authorized is False


def test_shorter_expiry_update_works_once_and_stale_token_cannot_repeat(tmp_path):
    clock, writer, reviewer, scope, original, retained = _state(tmp_path)
    clock[0] = 1500
    shorter = MemoryWrite(
        scope, "fixture-source", "updated", expires_at_ms=1900,
    )
    updated = generation_fenced_memory_update(
        reviewer, shorter, retained=retained,
    )
    assert updated.revision == 2
    assert updated.expires_at_ms == 1900
    assert updated.content == "updated"
    saved_events = writer.events(scope)

    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(writer, shorter, retained=retained)

    assert writer.events(scope) == saved_events
    assert writer.get(original.memory_id, scope, include_expired=True) == updated


def test_equal_existing_deadline_allowed_before_but_not_at_expiry(tmp_path):
    clock, writer, reviewer, scope, original, retained = _state(tmp_path)
    clock[0] = 1999
    same_deadline = MemoryWrite(
        scope, "fixture-source", "near-deadline", expires_at_ms=2000,
    )
    result = generation_fenced_memory_update(
        reviewer, same_deadline, retained=retained,
    )
    assert result.expires_at_ms == 2000
    refreshed = observe_memory_generation_for_cas(writer, scope, "fixture-source")
    events = writer.events(scope)
    clock[0] = 2000

    with pytest.raises(MemoryConflictError, match="source expired"):
        generation_fenced_memory_update(
            reviewer,
            MemoryWrite(
                scope, "fixture-source", "post-expiry", expires_at_ms=2500,
            ),
            retained=refreshed,
        )
    assert writer.events(scope) == events
    assert writer.get(original.memory_id, scope, include_expired=True) == result
