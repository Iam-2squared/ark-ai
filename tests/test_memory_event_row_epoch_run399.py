"""Ordinary Memory event readers validate every decoded row's input epoch.

Two real local event rows are enough to expose a transient change that a
final-only check would miss. No personal content, deletion or external action.
"""

from pathlib import Path

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import MemorySchemaError, SQLiteMemoryStore


@pytest.mark.parametrize("callback", ("memory_id", "event_constructor"))
@pytest.mark.parametrize("target", ("scope", "source"))
def test_event_hydration_rejects_transient_input_change_before_next_row(
    tmp_path, monkeypatch, callback, target,
):
    store = SQLiteMemoryStore(tmp_path / "events # %.sqlite", clock_ms=lambda: 50)
    scope = MemoryScope("test-owner", "private-fixture")
    store.put(MemoryWrite(scope, "one", "synthetic private one"))
    store.put(MemoryWrite(scope, "two", "synthetic private two"))
    original_source = store.path
    calls = 0

    def drift():
        if target == "source":
            store.path = Path(str(original_source))
        else:
            object.__setattr__(scope, "namespace", "other-namespace")

    if callback == "memory_id":
        original = memory_module._memory_id

        def checked_memory_id(value):
            nonlocal calls
            original(value)
            calls += 1
            if calls == 1:
                drift()

        monkeypatch.setattr(memory_module, "_memory_id", checked_memory_id)
    else:
        original = memory_module.MemoryEvent

        def checked_event(*args):
            nonlocal calls
            event = original(*args)
            calls += 1
            if calls == 1:
                drift()
            return event

        monkeypatch.setattr(memory_module, "MemoryEvent", checked_event)

    with pytest.raises(MemorySchemaError, match=f"memory events {target} changed"):
        store.events(scope)
    assert calls == 1

    monkeypatch.undo()
    store.path = original_source
    object.__setattr__(scope, "namespace", "private-fixture")
    # A failed read neither consumes nor changes saved event history.
    observed = store.events(scope)
    assert len(observed) == 2
    assert tuple(item.operation for item in observed) == ("create", "create")
    assert "synthetic private" not in repr(observed)
