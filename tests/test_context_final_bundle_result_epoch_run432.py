"""Last result-construction callbacks cannot promote altered Personal Context.

All contents are synthesized in disposable local SQLite; this is not consent,
private-data disclosure, or any real ToolBackend authorization.
"""

import pytest

import ark.personal_context_review as context
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "context.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    store.put(MemoryWrite(scope, "one", "private synthetic fixture"))
    snapshot = review_coherent_snapshot(
        store, CoherentSnapshotRequest(scope.owner_id, (scope.namespace,)),
    )
    return snapshot, context.ContextSelectionPolicy(5, 5)


def different_equal(value):
    replacement = ("!" + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize("target", (
    "wrong_type",
    "forged_digest",
    "equal_digest_carrier",
    "equal_items_tuple",
    "equal_item_content",
    "retarget_scope",
    "retarget_policy",
))
def test_context_bundle_constructor_cannot_replace_reviewed_selection(
    tmp_path, monkeypatch, target,
):
    snapshot, policy = fixture(tmp_path)
    original_type = context.SyntheticContextBundle

    def substituted_bundle(*args):
        if target == "wrong_type":
            return object()
        result = original_type(*args)
        if target == "forged_digest":
            object.__setattr__(result, "bundle_id", "ctx_bundle_" + "a" * 64)
        elif target == "equal_digest_carrier":
            object.__setattr__(
                result, "bundle_id", different_equal(result.bundle_id),
            )
        elif target == "equal_items_tuple":
            replacement = tuple(list(result.items))
            assert replacement == result.items and replacement is not result.items
            object.__setattr__(result, "items", replacement)
        elif target == "equal_item_content":
            item = result.items[0]
            object.__setattr__(item, "content", different_equal(item.content))
        elif target == "retarget_scope":
            object.__setattr__(snapshot.scopes[0], "namespace", "other-private")
        elif target == "retarget_policy":
            object.__setattr__(policy, "total_limit", 2)
        return result

    monkeypatch.setattr(context, "SyntheticContextBundle", substituted_bundle)
    with pytest.raises(
        context.PersonalContextReviewRejected,
        match="context bundle result changed|context selection result changed|context input changed",
    ):
        context.review_personal_context(snapshot, policy)


def test_unmodified_bundle_retains_original_selected_data_without_authority(tmp_path):
    snapshot, policy = fixture(tmp_path)
    bundle = context.review_personal_context(snapshot, policy)
    repeat = context.review_personal_context(snapshot, policy)
    assert type(bundle) is context.SyntheticContextBundle
    assert bundle == repeat
    assert len(bundle.items) == 1
    assert bundle.items[0].content == "private synthetic fixture"
    assert bundle.snapshot_digest == snapshot.provenance_sha256
    assert not bundle.action_authorized
    assert not bundle.dispatch_authorized
    assert "private synthetic fixture" not in bundle.bundle_id
