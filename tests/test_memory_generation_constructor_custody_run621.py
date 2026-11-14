"""Memory CAS witness constructors are inert and cannot be retargeted.

A token is local revision evidence, not owner consent or external action
authority. A rejected pre-COMMIT attempt must not imply any replay right.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import generation_fenced_cas as cas


@pytest.mark.parametrize("operation", ("observe", "update"))
def test_preinstalled_token_initializer_rejected_before_sqlite(
    tmp_path, monkeypatch, operation,
):
    store, scope, _, retained, proposed = make_case(tmp_path)
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("forged initializer executed")
        raise AssertionError("counterfeit initializer must not execute")

    def sqlite_forbidden(*_args, **_kwargs):
        raise AssertionError("SQLite must not start under a forged initializer")

    with monkeypatch.context() as patch:
        patch.setattr(cas.MemoryGenerationCASToken, "__init__", forbidden)
        connection = "_connect_readonly" if operation == "observe" else "_connect"
        patch.setattr(type(store), connection, sqlite_forbidden)
        with pytest.raises(
            cas.MemoryGenerationCASRejected, match="denial epoch changed",
        ):
            if operation == "observe":
                cas.observe_memory_generation_for_cas(store, scope, "stable")
            else:
                cas.generation_fenced_memory_update(
                    store, proposed, retained=retained,
                )

    assert calls == []


@pytest.mark.parametrize("operation", ("observe", "update"))
def test_digest_callback_cannot_install_token_initializer(
    tmp_path, monkeypatch, operation,
):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    original = cas._row_hash
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("forged initializer executed")
        raise AssertionError("counterfeit initializer must not execute")

    with monkeypatch.context() as patch:
        def on_row_digest(record):
            digest = original(record)
            patch.setattr(cas.MemoryGenerationCASToken, "__init__", forbidden)
            return digest

        patch.setattr(cas, "_row_hash", on_row_digest)
        with pytest.raises(
            cas.MemoryGenerationCASRejected, match="denial epoch changed",
        ):
            if operation == "observe":
                cas.observe_memory_generation_for_cas(store, scope, "stable")
            else:
                cas.generation_fenced_memory_update(
                    store, proposed, retained=retained,
                )

    assert calls == []
    assert store.get(saved.memory_id, scope).content == "original"
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_original_constructor_preserves_local_cas_without_external_authority(tmp_path):
    store, scope, _, retained, proposed = make_case(tmp_path)
    updated = cas.generation_fenced_memory_update(
        store, proposed, retained=retained,
    )
    observed = cas.observe_memory_generation_for_cas(store, scope, "stable")
    assert updated.revision == retained.revision + 1
    assert observed.last_event_id > retained.last_event_id
    assert observed.external_action_authorized is False
    assert observed.consent_authenticated is False
