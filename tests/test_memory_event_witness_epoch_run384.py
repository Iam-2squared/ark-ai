"""Offline Memory event witnesses cannot be reflectively substituted mid-replay."""

from pathlib import Path

import pytest

import ark.memory.synthetic_event_continuity_review as module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _setup(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "mem # %.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "namespace")
    genesis = module.review_synthetic_memory_event_continuity(store, scope)
    store.put(MemoryWrite(scope, "fixture", "FIRST"))
    first = module.review_synthetic_memory_event_continuity(store, scope)
    store.put(
        MemoryWrite(scope, "fixture", "SECOND"), expected_revision=1,
    )
    current = module.review_synthetic_memory_event_continuity(store, scope)
    return store, scope, genesis, first, current


@pytest.mark.parametrize("direction", ["advance", "rollback"])
def test_valid_retained_prefix_swap_during_hydration_fails_closed(
    tmp_path: Path, monkeypatch, direction: str,
):
    store, scope, genesis, first, current = _setup(tmp_path)
    retained = first if direction == "advance" else current
    replacement = current if direction == "advance" else genesis
    hydrate = module._record

    def reflected_mutation(row):
        record = hydrate(row)
        for name in ("scope_digest", "event_count", "last_event_id", "tail_hash"):
            object.__setattr__(retained, name, getattr(replacement, name))
        return record

    monkeypatch.setattr(module, "_record", reflected_mutation)
    with pytest.raises(module.SyntheticMemoryEventRejected, match="retained"):
        module.review_synthetic_memory_event_continuity(
            store, scope, retained=retained,
        )


def test_equal_value_path_rebind_during_hydration_is_rejected(
    tmp_path: Path, monkeypatch,
):
    store, scope, *_ = _setup(tmp_path)
    original = store.path
    hydrate = module._record

    def rebind_path(row):
        record = hydrate(row)
        store.path = Path(str(original))
        assert store.path == original and store.path is not original
        return record

    monkeypatch.setattr(module, "_record", rebind_path)
    with pytest.raises(module.SyntheticMemoryEventRejected, match="source"):
        module.review_synthetic_memory_event_continuity(store, scope)


def test_unchanged_retained_prefix_remains_readonly_and_inert(tmp_path: Path):
    store, scope, _genesis, first, _current = _setup(tmp_path)
    receipt = module.review_synthetic_memory_event_continuity(
        store, scope, retained=first,
    )
    assert receipt.event_count == 2
    assert receipt.deletion_authorized is False
    assert receipt.context_use_authorized is False
    assert receipt.external_disclosure_authorized is False
    assert "SECOND" not in repr(receipt)
