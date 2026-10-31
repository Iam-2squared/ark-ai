"""Disconnected Memory event replay rejects transient source/retained drift.

All rows are disposable synthetic fixtures; this witness never permits reuse,
deletion, export, or access to private Memory content.
"""

from pathlib import Path

import pytest

import ark.memory.synthetic_event_continuity_review as module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _state(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "event phase # %.sqlite", clock_ms=lambda: 9)
    scope = MemoryScope("synthetic-owner", "synthetic-space")
    store.put(MemoryWrite(scope, "first-source", "PRIVATE-TEST-A"))
    first = module.review_synthetic_memory_event_continuity(store, scope)
    store.put(MemoryWrite(scope, "second-source", "PRIVATE-TEST-B"))
    return store, scope, first


def _change(store, scope, retained, target, *, restore=False):
    if target == "source":
        if restore:
            store.path = _change.original_path
        else:
            _change.original_path = store.path
            store.path = Path(str(store.path))
    elif target == "scope":
        object.__setattr__(
            scope, "namespace", "synthetic-space" if restore else "other-space",
        )
    else:
        object.__setattr__(
            retained, "event_count", 1 if restore else 0,
        )


@pytest.mark.parametrize("target", ("source", "scope", "retained"))
def test_hydration_transient_change_cannot_hide_in_second_row(
    tmp_path: Path, monkeypatch, target: str,
):
    store, scope, first = _state(tmp_path)
    hydrate = module._record
    seen = 0

    def inject(row):
        nonlocal seen
        record = hydrate(row)
        seen += 1
        _change(store, scope, first, target, restore=(seen != 1))
        return record

    monkeypatch.setattr(module, "_record", inject)
    with pytest.raises(module.SyntheticMemoryEventRejected, match="source|retained"):
        module.review_synthetic_memory_event_continuity(
            store, scope, retained=first,
        )
    assert seen == 1


@pytest.mark.parametrize("target", ("source", "scope", "retained"))
def test_event_hash_transient_change_cannot_hide_in_second_event(
    tmp_path: Path, monkeypatch, target: str,
):
    store, scope, first = _state(tmp_path)
    digest = module._hash
    seen = 0

    def inject(label, values):
        nonlocal seen
        result = digest(label, values)
        if label == "ARK-synthetic-memory-event-v1":
            seen += 1
            _change(store, scope, first, target, restore=(seen != 1))
        return result

    monkeypatch.setattr(module, "_hash", inject)
    with pytest.raises(module.SyntheticMemoryEventRejected, match="source|retained"):
        module.review_synthetic_memory_event_continuity(
            store, scope, retained=first,
        )
    assert seen == 1


def test_empty_review_checks_epoch_after_schema_validation(tmp_path, monkeypatch):
    store = SQLiteMemoryStore(tmp_path / "empty.sqlite", clock_ms=lambda: 9)
    scope = MemoryScope("synthetic-owner", "empty-space")
    validate = module._validate_v1_schema

    def inject(connection):
        validate(connection)
        store.path = Path(str(store.path))

    monkeypatch.setattr(module, "_validate_v1_schema", inject)
    with pytest.raises(module.SyntheticMemoryEventRejected, match="source"):
        module.review_synthetic_memory_event_continuity(store, scope)


def test_unchanged_phases_remain_content_free_and_inert(tmp_path):
    store, scope, first = _state(tmp_path)
    current = module.review_synthetic_memory_event_continuity(
        store, scope, retained=first,
    )
    assert current.event_count == 2
    assert current.last_event_id > first.last_event_id
    assert current.deletion_authorized is False
    assert current.context_use_authorized is False
    assert current.external_disclosure_authorized is False
    assert "PRIVATE-TEST" not in repr(current)
