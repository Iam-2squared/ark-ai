"""Generation-fenced Memory CAS refuses substituted digest code before SQLite.

All state is local and synthetic. A retained CAS token is not a grant, consent,
an authenticated clock, or evidence of a successful external effect.
"""

from __future__ import annotations

import pytest

import ark.memory.generation_fenced_cas as generation
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    MemoryGenerationCASToken,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture():
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("synthetic-owner", "private-fixture")
    write = MemoryWrite(scope, "synthetic-source", "synthetic private content")
    token = MemoryGenerationCASToken(
        "mem_" + "a" * 64, 1, 1, 1, "b" * 64, "c" * 64,
    )
    return store, scope, write, token


def _install_hostile(patch, target: str, calls: list[str]) -> None:
    def hostile(*_args, **_kwargs):
        calls.append(target)
        raise AssertionError("hostile digest implementation ran")

    if target == "sha256":
        patch.setattr(generation.hashlib, "sha256", hostile)
    elif target == "json.dumps":
        patch.setattr(generation.json, "dumps", hostile)
    elif target == "event-domain":
        patch.setattr(generation, "_EVENT_DOMAIN", bytes(bytearray(generation._EVENT_DOMAIN)))
    else:
        patch.setattr(generation, "_ROW_DOMAIN", bytes(bytearray(generation._ROW_DOMAIN)))


@pytest.mark.parametrize(
    "target", ("sha256", "json.dumps", "event-domain", "row-domain"),
)
@pytest.mark.parametrize("operation", ("observe", "update", "token", "digest"))
def test_digest_dependency_change_is_denied_before_private_sqlite_read(
    monkeypatch: pytest.MonkeyPatch, target: str, operation: str,
) -> None:
    store, scope, write, token = _fixture()
    calls: list[str] = []
    with monkeypatch.context() as patch:
        _install_hostile(patch, target, calls)
        with pytest.raises(
            MemoryGenerationCASRejected, match="generation CAS digest dependencies changed",
        ):
            if operation == "observe":
                observe_memory_generation_for_cas(store, scope, write.source_id)
            elif operation == "update":
                generation_fenced_memory_update(store, write, retained=token)
            elif operation == "token":
                generation._token_fields(token)
            else:
                generation._digest(b"ARK-synthetic-domain\0", ["private fixture"])
    assert calls == []


def test_original_digest_dependencies_retain_local_non_authorizing_observation(
    tmp_path,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "local.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private-fixture")
    write = MemoryWrite(scope, "synthetic-source", "synthetic private content")
    stored = store.put(write)
    token = observe_memory_generation_for_cas(store, scope, write.source_id)
    assert token.memory_id == stored.memory_id
    assert token.revision == stored.revision == 1
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
