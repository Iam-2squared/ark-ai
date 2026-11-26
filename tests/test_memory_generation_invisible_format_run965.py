"""Run965: opt-in Memory CAS refuses additional invisible identity controls.

Frozen Memory v1 remains unchanged. Every SQLite file is disposable; a local
CAS token is neither consent nor a live tool authorization.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_INVISIBLE = (
    0x00AD, 0x034F, 0x180E, 0x200B, 0x200C, 0x200D,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064,
    0x206A, 0x206B, 0x206C, 0x206D, 0x206E, 0x206F, 0xFEFF,
)


@pytest.mark.parametrize("field", ("owner", "namespace", "source"))
@pytest.mark.parametrize("codepoint", _INVISIBLE, ids=lambda n: f"U+{n:04X}")
def test_invisible_generation_identity_rejected_before_local_cas(
    tmp_path, field: str, codepoint: int,
) -> None:
    path = tmp_path / "invisible-generation.sqlite3"
    base = MemoryScope("local-owner", "private")
    original = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    created = original.put(MemoryWrite(base, "source", "before"))
    retained = observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 101), base, "source",
    )
    invisible = chr(codepoint)
    scope = (
        MemoryScope("local" + invisible + "-owner", "private")
        if field == "owner"
        else MemoryScope("local-owner", "pri" + invisible + "vate")
        if field == "namespace"
        else base
    )
    source = "so" + invisible + "urce" if field == "source" else "source"

    with pytest.raises(MemoryGenerationCASRejected, match="formatting control"):
        observe_memory_generation_for_cas(
            SQLiteMemoryStore(path, clock_ms=lambda: 110), scope, source,
        )
    with pytest.raises(MemoryGenerationCASRejected, match="formatting control"):
        generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 120),
            MemoryWrite(scope, source, "should-not-commit"),
            retained=retained,
        )
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 130)
    record = cold.get(created.memory_id, base)
    assert record is not None
    assert record.content == "before"
    assert record.revision == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [("create", 1)]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False
