"""A retained generation CAS token cannot substitute executable field slots.

These are local SQLite fixtures. A token never authenticates consent, writer
identity, trusted time or permission for external effects/replay.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "generation-slot.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic", "private")
    store.put(MemoryWrite(scope, "fixture", "original"), expected_revision=0)
    retained = cas.observe_memory_generation_for_cas(store, scope, "fixture")
    return store, scope, retained


@pytest.mark.parametrize("field", (
    "memory_id", "revision", "event_prefix_sha256", "row_sha256",
    "__getattribute__",
))
@pytest.mark.parametrize("operation", ("observe", "update"))
def test_preinstalled_generation_token_slot_denied_before_sqlite(
    tmp_path, monkeypatch, field, operation,
):
    store, scope, retained = _case(tmp_path)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("forged token field lookup")
        raise AssertionError("forged generation token lookup executed")

    def no_sqlite(*_args, **_kwargs):
        raise AssertionError("SQLite opened before original token field check")

    with monkeypatch.context() as patch:
        patch.setattr(
            cas.MemoryGenerationCASToken, field,
            forbidden if field == "__getattribute__" else property(forbidden),
        )
        patch.setattr(
            store, "_connect_readonly" if operation == "observe" else "_connect",
            no_sqlite,
        )
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation token or denial epoch changed",
        ):
            if operation == "observe":
                cas.observe_memory_generation_for_cas(store, scope, "fixture")
            else:
                cas.generation_fenced_memory_update(
                    store, MemoryWrite(scope, "fixture", "proposed"),
                    retained=retained,
                )

    assert invoked == []
    assert store.get(retained.memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


@pytest.mark.parametrize("field", ("memory_id", "__getattribute__"))
def test_reentrant_clock_cannot_install_token_accessor_before_commit(
    tmp_path, monkeypatch, field,
):
    store, scope, retained = _case(tmp_path)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("forged token field lookup")
        raise AssertionError("forged generation token lookup executed")

    with monkeypatch.context() as patch:
        def clock():
            patch.setattr(
                cas.MemoryGenerationCASToken, field,
                forbidden if field == "__getattribute__" else property(forbidden),
            )
            return 1001

        patch.setattr(store, "_now", clock)
        with pytest.raises(
            cas.MemoryGenerationCASRejected,
            match="generation token or denial epoch changed",
        ):
            cas.generation_fenced_memory_update(
                store, MemoryWrite(scope, "fixture", "proposed"),
                retained=retained,
            )

    assert invoked == []
    assert store.get(retained.memory_id, scope).revision == 1
    assert store.get(retained.memory_id, scope).content == "original"
    assert len(store.events(scope)) == 1


def test_unmodified_generation_token_remains_local_and_non_authorizing(tmp_path):
    store, scope, retained = _case(tmp_path)
    record = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "fixture", "updated"), retained=retained,
    )
    assert record.revision == 2
    assert record.content == "updated"
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False
