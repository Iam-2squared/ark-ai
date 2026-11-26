"""Run963: opt-in Memory generation-CAS refuses audit-ambiguous identities.

These tests use only disposable local SQLite files. A generation token is
neither authenticated consent nor authority to execute an external action.
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

# C0 / DEL and the 15 Unicode formatting controls. These must be rejected
# at the *optional* CAS admission boundary, not by frozen Memory v1 objects.
_CONTROLS = (
    0x09, 0x0A, 0x1F, 0x7F, 0x85, 0x61C, 0x200E, 0x200F,
    0x2028, 0x2029, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2066, 0x2067, 0x2068, 0x2069,
)


@pytest.mark.parametrize("field", ("owner", "namespace", "source"))
@pytest.mark.parametrize("codepoint", _CONTROLS, ids=lambda n: f"U+{n:04X}")
def test_visual_control_identity_denied_before_memory_generation_cas(
    tmp_path, field: str, codepoint: int,
) -> None:
    path = tmp_path / "generation-format.sqlite"
    valid_scope = MemoryScope("owner", "private")
    valid_source = "source"
    base = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    created = base.put(MemoryWrite(valid_scope, valid_source, "before"))
    retained = observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 101), valid_scope, valid_source,
    )
    control = chr(codepoint)
    scope = (
        MemoryScope(f"owner{control}alternate", "private")
        if field == "owner" else
        MemoryScope("owner", f"private{control}alternate")
        if field == "namespace" else valid_scope
    )
    source = f"source{control}alternate" if field == "source" else valid_source
    proposed = MemoryWrite(scope, source, "after")

    with pytest.raises(MemoryGenerationCASRejected, match="formatting control"):
        observe_memory_generation_for_cas(
            SQLiteMemoryStore(path, clock_ms=lambda: 110), scope, source,
        )
    with pytest.raises(MemoryGenerationCASRejected, match="formatting control"):
        generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 120), proposed,
            retained=retained,
        )

    assert SQLiteMemoryStore(path, clock_ms=lambda: 130).get(
        created.memory_id, valid_scope,
    ).content == "before"
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT operation, revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [("create", 1)]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False


def test_multilingual_generation_identity_still_updates_exact_row(tmp_path) -> None:
    path = tmp_path / "generation-multilingual.sqlite"
    scope = MemoryScope("所有者", "研究")
    source = "文脈-資料"
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100).put(
        MemoryWrite(scope, source, "最初"),
    )
    retained = observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 101), scope, source,
    )
    updated = generation_fenced_memory_update(
        SQLiteMemoryStore(path, clock_ms=lambda: 200),
        MemoryWrite(scope, source, "更新"),
        retained=retained,
    )
    assert updated.memory_id == initial.memory_id
    assert updated.revision == 2
    assert updated.content == "更新"
    assert updated.scope == scope
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT operation, revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [("create", 1), ("update", 2)]
