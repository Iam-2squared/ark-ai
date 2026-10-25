"""Offline Personal Context carrier custody; no consent or disclosure authority."""

from pathlib import Path

import pytest

import ark.personal_context_reuse_review as reuse
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    review_fresh_nonrevoked_context,
)


def _state(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    memory.put(MemoryWrite(MemoryScope("owner-long", "profile"), "fixture", "private fixture"))
    request = CoherentSnapshotRequest("owner-long", ("profile",), "fixture")
    policy = ContextSelectionPolicy(4, 4)
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_fresh_nonrevoked_context(memory, request, policy, ledger)
    return memory, request, policy, ledger, cached


def _review(state):
    return reuse.review_synthetic_context_reuse(
        *state, captured_at_ms=100, now_ms=100, max_age_ms=10,
    )


@pytest.mark.parametrize("target,field", [
    ("request", "owner_id"),
    ("request", "namespaces"),
    ("request", "text"),
    ("policy", "policy_revision"),
])
def test_equal_valued_original_request_policy_carrier_retarget_is_rejected(
    tmp_path, monkeypatch, target, field,
):
    state = _state(tmp_path)
    carrier = state[1] if target == "request" else state[2]
    original = getattr(carrier, field)
    copy = tuple(list(original)) if type(original) is tuple else (original + "!")[:-1]
    assert copy == original and copy is not original
    reviewer = reuse.review_fresh_nonrevoked_context

    def replace_after_projection(*args, **kwargs):
        fresh = reviewer(*args, **kwargs)
        object.__setattr__(carrier, field, copy)
        return fresh

    monkeypatch.setattr(reuse, "review_fresh_nonrevoked_context", replace_after_projection)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="changed"):
        _review(state)


@pytest.mark.parametrize("field", ["items", "content", "bundle_id", "snapshot_digest"])
def test_equal_valued_cached_context_carrier_replacement_is_rejected(
    tmp_path, monkeypatch, field,
):
    state = _state(tmp_path)
    cached = state[4]
    reviewer = reuse.review_fresh_nonrevoked_context

    def replace_after_projection(*args, **kwargs):
        fresh = reviewer(*args, **kwargs)
        if field == "items":
            object.__setattr__(cached, "items", tuple(list(cached.items)))
        elif field == "content":
            item = cached.items[0]
            old = item.content
            clone = (old + "!")[:-1]
            assert clone is not old
            object.__setattr__(item, field, clone)
        else:
            old = getattr(cached, field)
            clone = (old + "!")[:-1]
            assert clone is not old
            object.__setattr__(cached, field, clone)
        return fresh

    monkeypatch.setattr(reuse, "review_fresh_nonrevoked_context", replace_after_projection)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="changed"):
        _review(state)


def test_source_path_retarget_inside_validation_constructor_denied(
    tmp_path, monkeypatch,
):
    state = _state(tmp_path)
    store = state[0]
    original_path = store.path
    init = ContextSelectionPolicy.__post_init__

    def retarget_during_constructor(self):
        init(self)
        store.path = Path(str(original_path))

    monkeypatch.setattr(ContextSelectionPolicy, "__post_init__", retarget_during_constructor)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="changed"):
        _review(state)
    assert store.path == original_path and store.path is not original_path


def test_receipt_construction_mutating_original_policy_is_denied(
    tmp_path, monkeypatch,
):
    state = _state(tmp_path)
    real_constructor = reuse.SyntheticContextReuseReview

    def retarget_during_result(*args, **kwargs):
        object.__setattr__(state[2], "policy_revision", "mutated")
        return real_constructor(*args, **kwargs)

    monkeypatch.setattr(reuse, "SyntheticContextReuseReview", retarget_during_result)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="changed"):
        _review(state)


def test_stable_context_reuse_remains_content_free_and_denied_by_default(tmp_path):
    result = _review(_state(tmp_path))
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert result.dispatch_authorized is False
    assert "private fixture" not in repr(result)
