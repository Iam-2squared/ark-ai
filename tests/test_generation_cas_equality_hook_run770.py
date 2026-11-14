"""Opt-in Memory generation CAS refuses executable equality/hash hooks.

Original frozen Memory v1 data contracts and SQLite schema are not changed.
No approval, consent, external effect or automatic retry is inferred.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


@pytest.mark.parametrize("target", ("scope", "write"))
@pytest.mark.parametrize("hook", ("__eq__", "__hash__"))
@pytest.mark.parametrize("entrypoint", ("observe", "update"))
def test_generation_guard_rejects_replaced_value_hooks_before_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    target: str, hook: str, entrypoint: str,
) -> None:
    scope = MemoryScope("owner-one", "local")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "source-one", "version-one"))
    token = observe_memory_generation_for_cas(store, scope, "source-one")
    proposed = MemoryWrite(scope, "source-one", "version-two")
    calls: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        calls.append("called")
        raise AssertionError("unreviewed equality/hash code executed")

    carrier = MemoryScope if target == "scope" else MemoryWrite
    with monkeypatch.context() as patch:
        patch.setattr(carrier, hook, forbidden)
        with pytest.raises(
            MemoryGenerationCASRejected,
            match="generation input carrier descriptor changed",
        ):
            if entrypoint == "observe":
                observe_memory_generation_for_cas(store, scope, "source-one")
            else:
                generation_fenced_memory_update(
                    store, proposed, retained=token,
                )
    assert calls == []
    actual = store.get(original.memory_id, scope)
    assert actual is not None
    assert actual.revision == 1
    assert actual.content == "version-one"
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
