"""Context selection must reject temporary privacy/provenance drift per item.

Offline Memory fixtures only; no disclosure or authority is created.
"""

import pytest

import ark.personal_context_review as context
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    memory.put(MemoryWrite(scope, "a", "synthetic first"))
    memory.put(MemoryWrite(scope, "b", "synthetic second"))
    snapshot = review_coherent_snapshot(
        memory, CoherentSnapshotRequest(
            scope.owner_id, (scope.namespace,), text="synthetic",
        ),
    )
    policy = context.ContextSelectionPolicy(3, 3)
    return snapshot, policy


def test_stable_context_preserves_bounded_disconnected_projection(tmp_path):
    snapshot, policy = _fixture(tmp_path)
    result = context.review_personal_context(snapshot, policy)
    assert len(result.items) == 2
    assert result.action_authorized is False
    assert result.dispatch_authorized is False


@pytest.mark.parametrize("target", ("record", "scope", "policy"))
def test_first_provenance_callback_drift_cannot_hide_until_next_item(
    tmp_path, monkeypatch, target,
):
    snapshot, policy = _fixture(tmp_path)
    record = snapshot.records[0][0]
    original_hash = context._hash
    count = 0

    def unstable_hash(label, payload):
        nonlocal count
        result = original_hash(label, payload)
        if label == "ARK-context-provenance-v1":
            count += 1
            if count == 1:
                if target == "record":
                    object.__setattr__(record, "content", "temporary tamper")
                elif target == "scope":
                    object.__setattr__(
                        snapshot.scopes[0], "namespace", "other-private",
                    )
                else:
                    object.__setattr__(policy, "total_limit", 2)
            elif count == 2:
                raise AssertionError(
                    "later provenance must not restore a previous mutation"
                )
        return result

    monkeypatch.setattr(context, "_hash", unstable_hash)
    with pytest.raises(
        context.PersonalContextReviewRejected, match="context input changed"
    ):
        context.review_personal_context(snapshot, policy)
    assert count == 1
