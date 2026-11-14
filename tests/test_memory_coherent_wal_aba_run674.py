"""Retained Memory row/event WAL snapshots across an ABA lifetime transition.

The second SQLite connection deletes and recreates the SAME memory identity
while a reader holds a WAL snapshot. Neither reader makes a writer-attribution,
consent, replay, or disclosure claim. No external compute or devices are used.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_row_delta_review import capture_local_memory_row_delta


def _case(tmp_path):
    path = tmp_path / "wal-generation-aba.sqlite"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("owner", "private")
    original = reader.put(MemoryWrite(scope, "source", "first private lifetime"))
    retained = (
        capture_local_memory_event_prefix(reader),
        review_memory_event_alignment(reader),
        capture_local_memory_row_delta(reader),
    )
    cas_token = observe_memory_generation_for_cas(reader, scope, "source")
    return reader, writer, scope, original, retained, cas_token


def _review(reader, retained):
    return coherent.review_retained_coherent_memory(
        reader, retained[0], retained[1], prior_rows=retained[2],
    )


def _aba(writer, scope, original):
    assert writer.delete(original.memory_id, scope, expected_revision=1)
    replacement = writer.put(
        MemoryWrite(scope, "source", "second private lifetime"),
        expected_revision=0,
    )
    assert replacement.memory_id == original.memory_id
    assert replacement.revision == 1
    return replacement


def test_wal_row_scan_preserves_old_complete_epoch_during_delete_recreate(
    tmp_path, monkeypatch,
):
    reader, writer, scope, original, retained, _ = _case(tmp_path)
    original_commitment = coherent.row_delta._commitment
    state = {"fired": False}

    def concurrent_aba(row):
        digest = original_commitment(row)
        if not state["fired"]:
            state["fired"] = True
            _aba(writer, scope, original)
        return digest

    monkeypatch.setattr(coherent.row_delta, "_commitment", concurrent_aba)
    before = _review(reader, retained)
    assert state["fired"] is True
    assert before.previous_event_count == before.current_event_count == 1
    assert before.row_count == 1
    assert before.retained_row_delta_checked is True
    assert before.memory_disclosure_authorized is False
    assert before.historical_writer_authenticated is False
    assert before.action_authorized is False

    after = _review(reader, retained)
    assert after.previous_event_count == 1
    assert after.current_event_count == 3
    assert after.row_count == 1
    assert after.retained_row_delta_checked is True
    assert after.historical_writer_authenticated is False
    assert after.action_authorized is False
    assert before.current_event_sha256 != after.current_event_sha256
    assert reader.get(original.memory_id, scope, include_expired=True).content == (
        "second private lifetime"
    )


def test_old_generation_token_cannot_update_recreated_row_after_wal_aba(tmp_path):
    reader, writer, scope, original, retained, token = _case(tmp_path)
    replacement = _aba(writer, scope, original)
    events = tuple(reader.events(scope))
    assert _review(reader, retained).current_event_count == 3

    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            reader,
            MemoryWrite(scope, "source", "must never overwrite replacement"),
            retained=token,
        )

    assert tuple(reader.events(scope)) == events
    assert reader.get(original.memory_id, scope, include_expired=True) == replacement
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False
