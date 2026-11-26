"""The first opt-in Memory generation hash cannot rebase private-read identity.

Only synthetic local fixture text is used. Mutations during the initial
deterministic_memory_id callback, including equal-valued replacement objects,
must fail *before* SQLite access. This does not change frozen Memory v1 or
authorize retry, external execution, privacy erasure or consent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _fresh_equal_text(value: str) -> str:
    copied = ("!" + value)[1:]
    assert copied == value and copied is not value
    return copied


@pytest.mark.parametrize("field", ("owner_id", "namespace", "path"))
@pytest.mark.parametrize("equal", (True, False))
def test_first_identity_digest_cannot_adopt_reentrant_new_scope_or_path(
    tmp_path, monkeypatch, field, equal,
):
    path = tmp_path / "private.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    old = store.put(MemoryWrite(scope, "source", "SYNTHETIC-PRIVATE"))
    retained = cas.observe_memory_generation_for_cas(store, scope, "source")
    assert retained.external_action_authorized is False

    real_id = cas.deterministic_memory_id
    hash_calls = []
    private_reads = []

    def reentrant_id(current_scope, current_source):
        hash_calls.append("hash")
        if field == "path":
            original = store.path
            replacement = Path(str(original)) if equal else tmp_path / "other.sqlite"
            assert replacement is not original
            store.path = replacement
        else:
            original = getattr(scope, field)
            replacement = _fresh_equal_text(original) if equal else "different"
            object.__setattr__(scope, field, replacement)
        return real_id(current_scope, current_source)

    def forbidden_private_read():
        private_reads.append("read")
        pytest.fail("reentrant first identity hashing reached private SQLite")

    monkeypatch.setattr(cas, "deterministic_memory_id", reentrant_id)
    monkeypatch.setattr(store, "_connect_readonly", forbidden_private_read)

    with pytest.raises(cas.MemoryGenerationCASRejected, match="input changed"):
        cas.observe_memory_generation_for_cas(store, scope, "source")
    assert hash_calls == ["hash"]
    assert private_reads == []

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert cold.get(old.memory_id, MemoryScope("fixture-owner", "private")).content == (
        "SYNTHETIC-PRIVATE"
    )
    assert len(cold.events(MemoryScope("fixture-owner", "private"))) == 1
    assert cas.MemoryGenerationCASToken.external_action_authorized.fget(retained) is False


def test_normal_initial_digest_retains_readonly_deny_only_token(tmp_path):
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(tmp_path / "normal.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "source", "SYNTHETIC"))
    token = cas.observe_memory_generation_for_cas(store, scope, "source")
    assert token.create_event_id == 1
    assert token.last_event_id == 1
    assert token.revision == 1
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
