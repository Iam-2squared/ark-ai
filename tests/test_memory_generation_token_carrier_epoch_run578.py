"""Equal-valued CAS token carrier replacement must fail inside the write epoch.

Synthetic SQLite clock callbacks only; never evidence of consent or permission
to dispatch an external tool, and an uncertain COMMIT must not be retried.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


@pytest.fixture
def local_generation(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "generation-carrier-epoch.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "source", "seed"), expected_revision=0)
    token = cas.observe_memory_generation_for_cas(store, scope, "source")
    return store, scope, token


@pytest.mark.parametrize("field", ("event_prefix_sha256", "row_sha256"))
def test_equal_valued_token_rebind_during_clock_rolls_back(
    local_generation, field,
):
    store, scope, token = local_generation
    before = getattr(token, field)
    equal_clone = ("!" + before)[1:]
    assert equal_clone == before
    assert equal_clone is not before

    def mutating_clock():
        object.__setattr__(token, field, equal_clone)
        return 1000

    store._clock_ms = mutating_clock
    with pytest.raises(
        cas.MemoryGenerationCASRejected, match="generation CAS inputs changed",
    ):
        cas.generation_fenced_memory_update(
            store, MemoryWrite(scope, "source", "should-not-save"),
            retained=token,
        )

    assert store.get(token.memory_id, scope).content == "seed"
    assert store.get(token.memory_id, scope).revision == 1
    assert len(store.events(scope)) == 1


def test_stable_original_token_permits_one_local_cas(local_generation):
    store, scope, token = local_generation
    updated = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", "next"), retained=token,
    )
    assert updated.revision == 2
    assert updated.content == "next"
    assert len(store.events(scope)) == 2
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
