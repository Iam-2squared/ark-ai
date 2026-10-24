"""Nested cached context values cannot change during a privacy recheck.

The tests are disconnected and store only synthetic Memory text. A passing
receipt never permits context use, external disclosure or ToolBackend dispatch.
"""

from pathlib import Path

import pytest

import ark.personal_context_reuse_review as module
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    review_fresh_nonrevoked_context,
)


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "profile")
    store.put(MemoryWrite(scope, "identity", "synthetic content"))
    request = CoherentSnapshotRequest("owner", ("profile",))
    policy = ContextSelectionPolicy(3, 3)
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_fresh_nonrevoked_context(store, request, policy, ledger)
    return store, request, policy, ledger, cached


def _review(state):
    return module.review_synthetic_context_reuse(
        *state, captured_at_ms=100, now_ms=100, max_age_ms=10,
    )


@pytest.mark.parametrize("field,replacement", [
    ("memory_id", "mem_" + "f" * 64),
    ("namespace", "unrelated"),
    ("content", "modified before recheck"),
    ("revision", 999),
    ("provenance_id", "ctx_" + "f" * 64),
])
def test_cached_nested_tamper_then_callback_restore_is_rejected(
    tmp_path: Path, monkeypatch, field: str, replacement: object,
):
    state = _fixture(tmp_path)
    item = state[4].items[0]
    object.__setattr__(item, field, replacement)
    actual = module.review_fresh_nonrevoked_context

    def restore_after_read(*args, **kwargs):
        fresh = actual(*args, **kwargs)
        object.__setattr__(item, field, getattr(fresh.items[0], field))
        return fresh

    monkeypatch.setattr(
        module, "review_fresh_nonrevoked_context", restore_after_read,
    )
    with pytest.raises(module.SyntheticContextReuseRejected, match="differs"):
        _review(state)


def test_cached_nested_non_exact_integer_rejected_before_read(tmp_path: Path):
    state = _fixture(tmp_path)
    object.__setattr__(state[4].items[0], "revision", True)
    with pytest.raises(module.SyntheticContextReuseRejected, match="shape"):
        _review(state)


def test_cached_items_reflected_to_list_during_read_are_rejected(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    actual = module.review_fresh_nonrevoked_context

    def replace_after_read(*args, **kwargs):
        fresh = actual(*args, **kwargs)
        object.__setattr__(state[4], "items", list(state[4].items))
        return fresh

    monkeypatch.setattr(module, "review_fresh_nonrevoked_context", replace_after_read)
    with pytest.raises(module.SyntheticContextReuseRejected, match="shape"):
        _review(state)


def test_untouched_cached_context_remains_inert(tmp_path: Path):
    value = _review(_fixture(tmp_path))
    assert value.context_use_authorized is False
    assert value.external_disclosure_authorized is False
    assert value.dispatch_authorized is False
    assert "synthetic content" not in repr(value)
