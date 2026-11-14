"""Equal-valued retained privacy evidence cannot be silently rebased.

Entirely synthetic, read-only review: never deletes personal information or
infers consent, human authorization, external disclosure or clock authenticity.
"""

import pytest

import ark.personal_context_retention_recheck_review as recheck
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    SyntheticRetentionItem,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _setup(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private-fixture")
    memory.put(MemoryWrite(
        scope, "mock-source", "private-content-never-returned",
        expires_at_ms=101,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, veto, now_ms=100,
    )
    return memory, scope, veto, cached


def _run(state, *, retained=None):
    return recheck.review_synthetic_retention_recheck(
        *state, now_ms=101, max_age_ms=10,
        retained_revocations=retained,
    )


def _clone_items(items):
    return tuple(
        SyntheticRetentionItem(item.memory_id, item.revision, item.state)
        for item in items
    )


def test_stable_retention_recheck_remains_diagnostic_only(tmp_path):
    state = _setup(tmp_path)
    result = _run(state)
    assert len(result.expired_memory_ids) == 1
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "private-content" not in repr(result)


def test_equal_cached_item_carrier_replacement_is_denied(tmp_path, monkeypatch):
    state = _setup(tmp_path)
    cached = state[3]
    original = recheck.review_synthetic_retention_inventory
    calls = 0

    def changed(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            object.__setattr__(cached, "items", _clone_items(cached.items))
        return result

    monkeypatch.setattr(recheck, "review_synthetic_retention_inventory", changed)
    with pytest.raises(
        recheck.SyntheticRetentionRecheckRejected,
        match="source or evidence changed",
    ):
        _run(state)
    assert calls == 1


def test_equal_current_item_carrier_replacement_is_denied(tmp_path, monkeypatch):
    state = _setup(tmp_path)
    original = recheck.review_synthetic_retention_inventory
    calls = 0
    current = None

    def changed(*args, **kwargs):
        nonlocal calls, current
        result = original(*args, **kwargs)
        calls += 1
        if calls == 2:
            current = result
        if calls == 3:
            object.__setattr__(current, "items", _clone_items(current.items))
        return result

    monkeypatch.setattr(recheck, "review_synthetic_retention_inventory", changed)
    with pytest.raises(
        recheck.SyntheticRetentionRecheckRejected,
        match="retention or revocation evidence drifted",
    ):
        _run(state)
    assert calls == 4


def test_equal_retained_revocation_tuple_replacement_is_denied(
    tmp_path, monkeypatch,
):
    memory, scope, veto, _ = _setup(tmp_path)
    veto.revoke(MemoryScope("unrelated", "fixture"), at_ms=100)
    cached = review_synthetic_retention_inventory(
        memory, scope, veto, now_ms=100,
    )
    retained = review_revocation_continuity(veto)
    assert retained.rows
    original = recheck.review_synthetic_retention_inventory
    calls = 0

    def changed(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            object.__setattr__(retained, "rows", tuple(list(retained.rows)))
        return result

    monkeypatch.setattr(recheck, "review_synthetic_retention_inventory", changed)
    with pytest.raises(
        recheck.SyntheticRetentionRecheckRejected,
        match="source or evidence changed",
    ):
        _run((memory, scope, veto, cached), retained=retained)
    assert calls == 1
