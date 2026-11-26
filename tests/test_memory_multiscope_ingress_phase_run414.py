"""Original Memory scope/source custody before the first hash callback.

Disposable local SQLite fixtures only. No consent, disclosure or schema change.
"""

from pathlib import Path

import pytest

import ark.memory.synthetic_multiscope_integrity_review as review
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "scope.sqlite", clock_ms=lambda: 30)
    scopes = (MemoryScope("owner", "first"), MemoryScope("owner", "second"))
    store.put(MemoryWrite(scopes[0], "source", "local-content"))
    return store, scopes


def _clone(value):
    result = ("!" + value)[1:]
    assert result == value and result is not value
    return result


@pytest.mark.parametrize("drift", ("source", "scope", "equal-carrier"))
def test_first_hash_callback_rejects_original_epoch(
    tmp_path, monkeypatch, drift,
):
    store, scopes = _fixture(tmp_path)
    original = review._scope_digest
    calls = []

    def changed(scope):
        calls.append(scope.namespace)
        digest = original(scope)
        if drift == "source":
            store.path = Path(str(store.path))
        elif drift == "scope":
            object.__setattr__(scopes[0], "namespace", "retargeted")
        else:
            object.__setattr__(
                scopes[0], "namespace", _clone(scopes[0].namespace),
            )
        return digest

    monkeypatch.setattr(review, "_scope_digest", changed)
    with pytest.raises(review.SyntheticMemorySnapshotRejected, match="scope or source"):
        review.review_synthetic_memory_scopes(store, scopes)
    assert len(calls) == 1  # never let the second hash restore the first drift


def test_original_scope_mutated_by_constructor_before_hash_is_rejected(
    tmp_path, monkeypatch,
):
    store, scopes = _fixture(tmp_path)
    post = MemoryScope.__post_init__
    seen = []

    def changed(self):
        post(self)
        seen.append(True)
        object.__setattr__(scopes[0], "owner_id", "other-owner")

    monkeypatch.setattr(MemoryScope, "__post_init__", changed)
    with pytest.raises(review.SyntheticMemorySnapshotRejected, match="scope or source"):
        review.review_synthetic_memory_scopes(store, scopes)
    assert seen


def test_unmodified_initial_hashes_still_produce_inert_snapshot(tmp_path):
    store, scopes = _fixture(tmp_path)
    witness = review.review_synthetic_memory_scopes(store, scopes)
    assert len(witness.scopes) == 2
    assert witness.context_use_authorized is False
    assert witness.external_disclosure_authorized is False
