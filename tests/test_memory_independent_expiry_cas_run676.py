"""Independent SQLite Memory CAS expiry, replay and scope boundary cases.

These fixtures never treat a local clock or an advisory generation token as
trusted time, consent, durable caller identity or authority for external work.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_cas_outcome_review import review_memory_generation_cas_outcome
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _pair(tmp_path, expires_at_ms):
    path = tmp_path / "expiry-concurrency.sqlite"
    clock = {"now": 1000}
    current = SQLiteMemoryStore(path, clock_ms=lambda: clock["now"])
    other = SQLiteMemoryStore(path, clock_ms=lambda: clock["now"])
    scope = MemoryScope("offline-owner", "private")
    initial = current.put(MemoryWrite(
        scope, "retained", "initial private content", expires_at_ms=expires_at_ms,
    ))
    token = observe_memory_generation_for_cas(current, scope, "retained")
    return current, other, scope, clock, initial, token


@pytest.mark.parametrize(
    ("now", "proposed_expiry"),
    (
        (1001, 1401),  # extension never becomes implicit consent
        (1001, None),  # clearing an existing expiry is likewise forbidden
        (1400, 1400),  # exact expiry equality is expired, not writable
        (1401, 1300),  # a past proposal cannot resurrect an expired source
        (999, 1300),  # a regressed caller clock must not rewrite history
    ),
)
def test_independent_connection_expiry_cas_denial_is_atomic(
    tmp_path, now, proposed_expiry,
):
    reader, other, scope, clock, original, token = _pair(tmp_path, 1400)
    clock["now"] = now
    before = tuple(other.events(scope))
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            other, MemoryWrite(
                scope, "retained", "must not replace",
                expires_at_ms=proposed_expiry,
            ), retained=token,
        )
    assert tuple(reader.events(scope)) == before
    assert reader.get(original.memory_id, scope, include_expired=True) == original
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False


def test_independent_writer_shortens_retention_and_stale_token_cannot_restore_it(tmp_path):
    reader, other, scope, clock, original, token = _pair(tmp_path, 1400)
    clock["now"] = 1100
    shortened = generation_fenced_memory_update(
        other, MemoryWrite(
            scope, "retained", "new private content", expires_at_ms=1200,
        ), retained=token,
    )
    before = tuple(reader.events(scope))
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            reader, MemoryWrite(
                scope, "retained", "attempted stale overwrite", expires_at_ms=1400,
            ), retained=token,
        )
    assert shortened.revision == original.revision + 1
    assert reader.get(original.memory_id, scope, include_expired=True) == shortened
    assert tuple(reader.events(scope)) == before
    outcome = review_memory_generation_cas_outcome(
        reader, MemoryWrite(
            scope, "retained", "attempted stale overwrite", expires_at_ms=1400,
        ), retained=token,
    )
    assert outcome.automatic_retry_authorized is False
    assert outcome.commit_attributed_to_caller is False


def test_other_namespace_write_does_not_invalidate_exact_row_generation(tmp_path):
    reader, other, scope, clock, original, token = _pair(tmp_path, None)
    independent = MemoryScope(scope.owner_id, "shared-fixture")
    other.put(MemoryWrite(independent, "retained", "other scope content"))
    clock["now"] = 1100
    committed = generation_fenced_memory_update(
        reader, MemoryWrite(scope, "retained", "scoped update"),
        retained=token,
    )
    assert committed.revision == 2
    assert committed.scope == scope
    assert committed.memory_id == original.memory_id
    assert other.get(committed.memory_id, scope, include_expired=True) == committed
    assert len(tuple(reader.events(independent))) == 1


def test_cross_namespace_generation_token_reuse_is_rejected_before_write(tmp_path):
    reader, other, scope, _clock, original, token = _pair(tmp_path, None)
    independent = MemoryScope(scope.owner_id, "another-private-scope")
    before = tuple(reader.events(scope))
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            other, MemoryWrite(independent, "retained", "not my generation"),
            retained=token,
        )
    assert tuple(reader.events(scope)) == before
    assert reader.get(original.memory_id, scope, include_expired=True) == original
    assert other.search.__self__ is other
