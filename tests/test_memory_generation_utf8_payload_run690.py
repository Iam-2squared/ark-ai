"""Generation CAS never feeds ill-formed UTF-8 payloads into SQLite.

Memory v1 permits Unicode code units that SQLite cannot persist. The optional
generation-fenced update rejects malformed content/metadata before BEGIN
IMMEDIATE; a rejection consumes no revision and does not authorize retry of
an outcome-unknown write. Fixtures contain no real private information.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("content", "metadata"),
    (
        ("\ud800", {"label": "valid"}),
        ("\udfff", {"label": "valid"}),
        ("valid", {"\ud800": "value"}),
        ("valid", {"label": "\udfff"}),
    ),
)
def test_non_utf8_cas_payload_is_rejected_without_consuming_token(
    tmp_path, content, metadata,
):
    clock = [100]
    path = tmp_path / "private.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    old = first.put(MemoryWrite(scope, "fixture", "original", expires_at_ms=500))
    token = observe_memory_generation_for_cas(first, scope, "fixture")
    assert token.external_action_authorized is False
    clock[0] = 200

    with pytest.raises(MemoryGenerationCASRejected, match="not valid UTF-8"):
        generation_fenced_memory_update(
            first,
            MemoryWrite(scope, "fixture", content, metadata, expires_at_ms=500),
            retained=token,
        )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    unchanged = cold.get(old.memory_id, scope)
    assert unchanged.content == "original"
    assert unchanged.revision == 1
    assert unchanged.expires_at_ms == 500
    assert len(cold.events(scope)) == 1
    assert observe_memory_generation_for_cas(cold, scope, "fixture") == token

    # A *definitively rejected* pre-transaction request did not consume CAS.
    # This is not permission to replay a commit-unknown request.
    accepted = generation_fenced_memory_update(
        cold, MemoryWrite(scope, "fixture", "safe", expires_at_ms=500),
        retained=token,
    )
    assert accepted.revision == 2
    assert len(cold.events(scope)) == 2


@pytest.mark.parametrize(
    ("content", "metadata"),
    (
        ("🧪 synthetic", {"label": "unicode"}),
        ("日本語のテスト", {"場所": "山"}),
    ),
)
def test_valid_multibyte_payload_is_still_accepted(tmp_path, content, metadata):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    memory = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    record = memory.put(MemoryWrite(scope, "fixture", "before", expires_at_ms=300))
    retained = observe_memory_generation_for_cas(memory, scope, "fixture")
    updated = generation_fenced_memory_update(
        memory,
        MemoryWrite(scope, "fixture", content, metadata, expires_at_ms=300),
        retained=retained,
    )
    assert updated.revision == 2
    assert updated.content == content
    assert dict(updated.metadata) == metadata
    assert updated.expires_at_ms == 300
    assert len(memory.events(scope)) == 2
    assert SQLiteMemoryStore(
        path, clock_ms=lambda: 100,
    ).get(record.memory_id, scope).content == content
