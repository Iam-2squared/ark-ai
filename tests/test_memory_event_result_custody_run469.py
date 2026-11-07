"""Memory event history must not expose forged or reflectively retargeted results.

Only disposable local SQLite fixtures are used; no personal data or actions.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_store as storage
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _events(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "events.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("synthetic-owner", "private-fixture")
    store.put(MemoryWrite(scope, "a", "private fixture a"))
    store.put(MemoryWrite(scope, "b", "private fixture b"))
    return store, scope


def test_real_event_results_preserve_scope_and_order_without_private_content(tmp_path):
    store, scope = _events(tmp_path)
    observed = store.events(scope)
    assert tuple(event.event_id for event in observed) == (1, 2)
    assert tuple(event.operation for event in observed) == ("create", "create")
    assert all(type(event) is storage.MemoryEvent for event in observed)
    assert "private fixture" not in repr(observed)


def test_event_reader_rejects_substituted_result_class(tmp_path, monkeypatch):
    store, scope = _events(tmp_path)
    original = storage.MemoryEvent

    class ForgedEvent(original):
        pass

    monkeypatch.setattr(storage, "MemoryEvent", ForgedEvent)
    with pytest.raises(MemorySchemaError, match="event result changed"):
        store.events(scope)


@pytest.mark.parametrize("field", ("scope", "operation", "memory_id"))
def test_event_reader_rejects_value_equal_result_carrier_replacement(
    tmp_path, monkeypatch, field,
):
    store, scope = _events(tmp_path)
    original = storage.MemoryEvent

    def constructed(*args):
        event = original(*args)
        if field == "scope":
            object.__setattr__(
                event, "scope",
                MemoryScope(event.scope.owner_id, event.scope.namespace),
            )
        else:
            prior = getattr(event, field)
            replacement = ("~" + prior)[1:]
            assert replacement == prior and replacement is not prior
            object.__setattr__(event, field, replacement)
        return event

    monkeypatch.setattr(storage, "MemoryEvent", constructed)
    with pytest.raises(MemorySchemaError, match="event result changed"):
        store.events(scope)


def test_later_event_constructor_cannot_retarget_prior_result(tmp_path, monkeypatch):
    store, scope = _events(tmp_path)
    original = storage.MemoryEvent
    first = None

    def constructed(*args):
        nonlocal first
        result = original(*args)
        if first is None:
            first = result
        else:
            object.__setattr__(first, "revision", 999)
        return result

    monkeypatch.setattr(storage, "MemoryEvent", constructed)
    with pytest.raises(MemorySchemaError, match="event result changed"):
        store.events(scope)
    assert first is not None


def test_event_result_scope_fields_remain_original_across_later_rows(
    tmp_path, monkeypatch,
):
    store, scope = _events(tmp_path)
    original = storage.MemoryEvent
    first = None

    def constructed(*args):
        nonlocal first
        result = original(*args)
        if first is None:
            first = result
        else:
            object.__setattr__(first.scope, "namespace", "retargeted")
        return result

    monkeypatch.setattr(storage, "MemoryEvent", constructed)
    with pytest.raises(MemorySchemaError, match="event result changed"):
        store.events(scope)
