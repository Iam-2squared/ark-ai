"""Retention cached nested values must be epoch-pinned across callbacks."""

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
    review_synthetic_retention_recheck,
)
from ark.personal_context_retention_review import (
    RetentionState,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "private")
    store.put(MemoryWrite(
        scope, "first", "PRIVATE-CONTENT-DO-NOT-LOG", expires_at_ms=105,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(store, scope, veto, now_ms=100)
    return store, scope, veto, cached


def review(state):
    store, scope, veto, cached = state
    return review_synthetic_retention_recheck(
        store, scope, veto, cached, now_ms=101, max_age_ms=10,
    )


def test_ordinary_readonly_recheck_does_not_grant_use_or_deletion(tmp_path: Path):
    value = review(fixture(tmp_path))
    assert value.deletion_authorized is False
    assert value.erasure_completed is False
    assert value.context_use_authorized is False
    assert value.external_disclosure_authorized is False
    assert "PRIVATE-CONTENT" not in repr(value)


@pytest.mark.parametrize("column", ["memory_id", "revision", "state"])
def test_reflected_nested_item_mutation_during_second_read_is_denied(
    tmp_path: Path, monkeypatch, column: str,
):
    import ark.personal_context_retention_recheck_review as module

    state = fixture(tmp_path)
    original = module.review_synthetic_retention_inventory
    called = 0

    def injected(*args, **kwargs):
        nonlocal called
        result = original(*args, **kwargs)
        called += 1
        if called == 2:
            item = state[3].items[0]
            replacement = {
                "memory_id": "mem_" + "0" * 64,
                "revision": 800,
                "state": RetentionState.EXPIRED,
            }[column]
            object.__setattr__(item, column, replacement)
        return result

    monkeypatch.setattr(module, "review_synthetic_retention_inventory", injected)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="changed|drifted"):
        review(state)


def test_non_tuple_nested_items_reflected_during_read_are_denied(
    tmp_path: Path, monkeypatch,
):
    import ark.personal_context_retention_recheck_review as module

    state = fixture(tmp_path)
    original = module.review_synthetic_retention_inventory
    called = 0

    def injected(*args, **kwargs):
        nonlocal called
        result = original(*args, **kwargs)
        called += 1
        if called == 2:
            object.__setattr__(state[3], "items", list(state[3].items))
        return result

    monkeypatch.setattr(module, "review_synthetic_retention_inventory", injected)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="exact"):
        review(state)


def test_malformed_items_at_entry_are_rejected(tmp_path: Path):
    state = fixture(tmp_path)
    object.__setattr__(state[3], "items", (object(),))
    with pytest.raises(SyntheticRetentionRecheckRejected, match="exact"):
        review(state)
