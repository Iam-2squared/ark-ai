"""Synthetic privacy rechecks must pin intent and source identities.

All cases are disconnected fixtures; a diagnostic result cannot authorize
personal-data processing, disclosure, or tool execution.
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


def _state(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "profile")
    store.put(MemoryWrite(scope, "fixture", "OFFLINE-ONLY"))
    request = CoherentSnapshotRequest("owner", ("profile",))
    policy = ContextSelectionPolicy(4, 4)
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    cached = review_fresh_nonrevoked_context(store, request, policy, ledger)
    return store, request, policy, ledger, cached


def _review(state):
    return module.review_synthetic_context_reuse(
        *state, captured_at_ms=100, now_ms=100, max_age_ms=10,
    )


@pytest.mark.parametrize("target,field,value", [
    ("request", "owner_id", "other-owner"),
    ("request", "text", "changed selection query"),
    ("request", "per_namespace_limit", 1),
    ("request", "include_expired", True),
    ("policy", "total_limit", 1),
    ("policy", "per_namespace_limit", 1),
    ("policy", "policy_revision", "changed_fixture_revision"),
])
def test_reentrant_input_change_after_projection_is_rejected(
    tmp_path: Path, monkeypatch, target: str, field: str, value: object,
):
    state = _state(tmp_path)
    original = module.review_fresh_nonrevoked_context
    carrier = state[1] if target == "request" else state[2]

    def change_after_read(*args, **kwargs):
        fresh = original(*args, **kwargs)
        object.__setattr__(carrier, field, value)
        return fresh

    monkeypatch.setattr(module, "review_fresh_nonrevoked_context", change_after_read)
    with pytest.raises(module.SyntheticContextReuseRejected, match="changed"):
        _review(state)


@pytest.mark.parametrize("target", ["memory", "revocation"])
def test_reentrant_storage_retarget_after_projection_is_rejected(
    tmp_path: Path, monkeypatch, target: str,
):
    state = _state(tmp_path)
    original = module.review_fresh_nonrevoked_context
    carrier = state[0] if target == "memory" else state[3]

    def change_after_read(*args, **kwargs):
        fresh = original(*args, **kwargs)
        carrier.path = tmp_path / ("retargeted-" + target + ".sqlite")
        return fresh

    monkeypatch.setattr(module, "review_fresh_nonrevoked_context", change_after_read)
    with pytest.raises(module.SyntheticContextReuseRejected, match="changed"):
        _review(state)


def test_unmodified_intent_and_storage_remain_inert(tmp_path: Path):
    receipt = _review(_state(tmp_path))
    assert receipt.context_use_authorized is False
    assert receipt.external_disclosure_authorized is False
    assert receipt.dispatch_authorized is False
    assert "OFFLINE-ONLY" not in repr(receipt)
