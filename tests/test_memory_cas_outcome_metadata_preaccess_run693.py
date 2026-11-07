"""Post-COMMIT generation CAS review rejects malformed metadata before SQLite.

Memory v1 is frozen; these are opt-in diagnostic safeguards on a reflectively
changed proposed MemoryWrite, with no external action or automatic retry.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    MemoryCASOutcomeRejected,
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas


@pytest.mark.parametrize(
    "mutated",
    (
        {"\ud800": "value"},
        {"label": "\udfff"},
        {"label": 4},
        {"label": "x" * 4097},
        {"label": "value", "": "bad"},
        {str(i): "v" for i in range(65)},
    ),
)
def test_invalid_metadata_rejected_before_private_snapshot(
    tmp_path, monkeypatch, mutated,
):
    scope = MemoryScope("fixture-owner", "private")
    path = tmp_path / "source.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "synthetic-source", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "synthetic-source")
    proposed = MemoryWrite(scope, "synthetic-source", "after")
    object.__setattr__(proposed, "metadata", mutated)
    opened = []

    def forbidden_private_read():
        opened.append(True)
        pytest.fail("invalid opt-in review metadata must not open SQLite")

    monkeypatch.setattr(store, "_connect_readonly", forbidden_private_read)
    with pytest.raises(MemoryCASOutcomeRejected, match="metadata"):
        review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert opened == []

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert cold.get(original.memory_id, scope).content == "before"
    assert len(cold.events(scope)) == 1
    assert observe_memory_generation_for_cas(cold, scope, "synthetic-source") == retained


def test_valid_utf8_metadata_keeps_manual_only_review(tmp_path):
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(tmp_path / "source.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "synthetic-source", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "synthetic-source")
    proposed = MemoryWrite(
        scope, "synthetic-source", "after",
        {"場所": "山", "label": "🧪"},
    )
    report = review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert report.observation == "UNCHANGED_OBSERVED"
    assert report.commit_attributed_to_caller is False
    assert report.automatic_retry_authorized is False
    assert report.external_action_authorized is False
