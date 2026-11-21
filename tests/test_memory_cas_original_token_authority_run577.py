"""CAS token authority must retain the original denial code across restarts.

All probes are local SQLite fixtures. A substituted false-only descriptor is
not permission to observe a generation or begin a write transaction.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


@pytest.fixture
def local_row(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "cas-original-denials.sqlite", clock_ms=lambda: 1_000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "source", "seed"), expected_revision=0)
    retained = cas.observe_memory_generation_for_cas(store, scope, "source")
    return store, scope, retained


@pytest.mark.parametrize(
    "flag", ("external_action_authorized", "consent_authenticated"),
)
@pytest.mark.parametrize("operation", ("observe", "update"))
def test_preinstalled_false_only_token_denial_rejected_before_db(
    local_row, monkeypatch, flag, operation,
):
    store, scope, retained = local_row
    openings = []

    def forbidden(self):
        openings.append(True)
        raise AssertionError("SQLite must not open under altered token authority")

    # Install the fake authority BEFORE either public entry point begins.
    with monkeypatch.context() as changes:
        changes.setattr(
            cas.MemoryGenerationCASToken, flag, property(lambda _self: False),
        )
        changes.setattr(
            SQLiteMemoryStore,
            "_connect_readonly" if operation == "observe" else "_connect",
            forbidden,
        )
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation token or denial epoch changed",
        ):
            if operation == "observe":
                cas.observe_memory_generation_for_cas(store, scope, "source")
            else:
                cas.generation_fenced_memory_update(
                    store, MemoryWrite(scope, "source", "next"),
                    retained=retained,
                )

    assert openings == []
    assert store.get(retained.memory_id, scope).revision == 1
    assert len(store.events(scope)) == 1


def test_original_denials_allow_local_generation_observation_and_cas(local_row):
    store, scope, retained = local_row
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False
    record = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", "updated"), retained=retained,
    )
    assert record.revision == 2
    assert store.get(record.memory_id, scope).content == "updated"
    assert len(store.events(scope)) == 2
