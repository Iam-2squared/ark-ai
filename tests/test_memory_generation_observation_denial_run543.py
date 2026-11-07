"""Generation CAS observation stays non-authorizing after denial callbacks."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "generation.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("offline-fixture", "private")
    store.put(MemoryWrite(scope, "source", "seed"), expected_revision=0)
    return store, scope


@pytest.mark.parametrize(
    "denial", ("external_action_authorized", "consent_authenticated"),
)
def test_false_denial_getter_cannot_retarget_observed_token(
    tmp_path, monkeypatch, denial,
):
    store, scope = _fixture(tmp_path)

    def mutate(self):
        object.__setattr__(self, "event_prefix_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        cas.MemoryGenerationCASToken, denial, property(mutate),
    )
    with pytest.raises(
        cas.MemoryGenerationCASRejected,
        match="generation token or denial epoch changed",
    ):
        cas.observe_memory_generation_for_cas(store, scope, "source")
    assert len(store.events(scope)) == 1


@pytest.mark.parametrize("replacement", (True, False))
def test_late_denial_cannot_replace_first_permission_property(
    tmp_path, monkeypatch, replacement,
):
    store, scope = _fixture(tmp_path)
    token_type = cas.MemoryGenerationCASToken

    def mutate(self):
        monkeypatch.setattr(
            token_type, "external_action_authorized",
            property(lambda other: replacement),
        )
        return False

    monkeypatch.setattr(token_type, "consent_authenticated", property(mutate))
    with pytest.raises(
        cas.MemoryGenerationCASRejected,
        match="generation token or denial epoch changed",
    ):
        cas.observe_memory_generation_for_cas(store, scope, "source")


def test_normal_token_is_observed_without_write_authority(tmp_path):
    store, scope = _fixture(tmp_path)
    token = cas.observe_memory_generation_for_cas(store, scope, "source")
    assert token.revision == 1
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
