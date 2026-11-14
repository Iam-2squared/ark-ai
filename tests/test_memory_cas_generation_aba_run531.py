"""Local-only Memory v1 CAS generation ambiguity tests.

Revision 1 can recur after a deterministic memory ID is recreated. The
diagnostic reports that hazard without changing frozen write contracts.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as mod


def _fixture(tmp_path):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    return path, store, scope


def _put(store, scope, content, *, revision=0):
    return store.put(
        MemoryWrite(scope, "deterministic-source", content),
        expected_revision=revision,
    )


def _review(store, scope, revision):
    return mod.review_memory_revision_reuse(
        store, scope, "deterministic-source", expected_revision=revision,
    )


def test_first_generation_cas_revision_has_no_reuse_warning(tmp_path):
    _, store, scope = _fixture(tmp_path)
    first = _put(store, scope, "first")
    report = _review(store, scope, first.revision)
    assert report.generation_count == 1
    assert report.event_count == 1
    assert report.live_revision == 1
    assert report.revision_reuse_possible is False
    assert report.write_authorized is False
    assert report.erase_authorized is False
    assert report.generation_authenticated is False


def test_delete_and_recreate_same_id_exposes_cas_aba_revision_hazard(tmp_path):
    path, first_handle, scope = _fixture(tmp_path)
    original = _put(first_handle, scope, "original")
    assert first_handle.delete(
        original.memory_id, scope, expected_revision=1,
    ) is True
    second_handle = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    restarted = _put(second_handle, scope, "new lifetime")
    assert restarted.memory_id == original.memory_id
    assert restarted.revision == original.revision == 1
    report = _review(first_handle, scope, original.revision)
    assert report.generation_count == 2
    assert report.event_count == 3
    assert report.live_revision == 1
    assert report.revision_reuse_possible is True
    assert second_handle.get(original.memory_id, scope).content == "new lifetime"


def test_later_revision_cannot_erase_generation_reuse_evidence(tmp_path):
    _, store, scope = _fixture(tmp_path)
    initial = _put(store, scope, "initial")
    store.delete(initial.memory_id, scope, expected_revision=1)
    renewed = _put(store, scope, "renewed")
    changed = _put(store, scope, "updated", revision=renewed.revision)
    assert changed.revision == 2
    assert _review(store, scope, 1).revision_reuse_possible is False
    report = _review(store, scope, changed.revision)
    assert report.generation_count == 2
    assert report.revision_reuse_possible is True


def test_terminal_generation_has_no_live_cas_authority(tmp_path):
    _, store, scope = _fixture(tmp_path)
    item = _put(store, scope, "temporary")
    store.delete(item.memory_id, scope, expected_revision=1)
    result = _review(store, scope, 1)
    assert result.generation_count == 1
    assert result.event_count == 2
    assert result.live_revision is None
    assert result.revision_reuse_possible is False


def test_never_created_source_has_no_invented_history(tmp_path):
    _, store, scope = _fixture(tmp_path)
    result = _review(store, scope, 0)
    assert result.generation_count == 0
    assert result.event_count == 0
    assert result.live_revision is None
    assert result.revision_reuse_possible is False


@pytest.mark.parametrize("tamper", ("missing_first", "wrong_scope", "wrong_revision"))
def test_memory_history_tampering_fails_closed(tmp_path, tamper):
    path, store, scope = _fixture(tmp_path)
    first = _put(store, scope, "first")
    _put(store, scope, "second", revision=first.revision)
    with sqlite3.connect(path) as conn:
        if tamper == "missing_first":
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=? AND operation='create'",
                (first.memory_id,),
            )
        elif tamper == "wrong_scope":
            conn.execute(
                "UPDATE memory_events SET namespace='foreign' "
                "WHERE memory_id=? AND operation='update'",
                (first.memory_id,),
            )
        else:
            conn.execute(
                "UPDATE memory_events SET revision=9 "
                "WHERE memory_id=? AND operation='update'",
                (first.memory_id,),
            )
    with pytest.raises(mod.MemoryGenerationReviewRejected):
        _review(store, scope, 2)


def test_bounded_scan_refuses_partial_generation_history(tmp_path, monkeypatch):
    _, store, scope = _fixture(tmp_path)
    first = _put(store, scope, "first")
    _put(store, scope, "second", revision=first.revision)
    monkeypatch.setattr(mod, "_MAX_EVENTS", 1)
    with pytest.raises(mod.MemoryGenerationReviewRejected, match="bounded"):
        _review(store, scope, 2)


@pytest.mark.parametrize("value", (True, 1.0, -1, 2**63, "1"))
def test_cas_expected_revision_requires_exact_bounded_integer(tmp_path, value):
    _, store, scope = _fixture(tmp_path)
    with pytest.raises(mod.MemoryGenerationReviewRejected, match="exact bounded"):
        _review(store, scope, value)


def test_report_is_read_only_and_does_not_change_event_history(tmp_path):
    _, store, scope = _fixture(tmp_path)
    _put(store, scope, "no deletion")
    before = [(event.event_id, event.operation) for event in store.events(scope)]
    first = _review(store, scope, 1)
    second = _review(store, scope, 1)
    assert first == second
    assert [(event.event_id, event.operation) for event in store.events(scope)] == before
