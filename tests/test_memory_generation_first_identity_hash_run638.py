"""Do not adopt a new Memory source during the FIRST identity hash.

The fixture uses a private temporary SQLite file and never modifies the
frozen Memory schema or grants any write/erasure authority.
"""

from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as review


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("only-local-owner", "private")
    store.put(MemoryWrite(scope, "source", "PRIVATE-FIXTURE"))
    return store, scope


def _equal_new_text(value):
    other = ("~" + value)[1:]
    assert other == value and other is not value
    return other


@pytest.mark.parametrize("field", ("owner", "namespace", "path"))
@pytest.mark.parametrize("equal", (True, False))
def test_first_identity_hash_cannot_rebase_original_memory_inputs(
    tmp_path, monkeypatch, field, equal,
):
    store, scope = _case(tmp_path)
    real_hash = review.deterministic_memory_id
    hash_calls = []
    database_reads = []

    def no_private_read():
        database_reads.append("read")
        raise AssertionError("no private SQLite read after source changed")

    def reentrant_hash(current_scope, current_source):
        hash_calls.append("hash")
        if field == "path":
            original = store.path
            store.path = Path(str(original)) if equal else tmp_path / "other.sqlite"
            assert store.path is not original
        else:
            name = "owner_id" if field == "owner" else "namespace"
            original = getattr(scope, name)
            changed = _equal_new_text(original) if equal else "other-value"
            object.__setattr__(scope, name, changed)
        return real_hash(current_scope, current_source)

    monkeypatch.setattr(review, "deterministic_memory_id", reentrant_hash)
    monkeypatch.setattr(store, "_connect_readonly", no_private_read)
    with pytest.raises(
        review.MemoryGenerationReviewRejected,
        match="generation source changed during review",
    ):
        review.review_memory_revision_reuse(
            store, scope, "source", expected_revision=1,
        )
    assert hash_calls == ["hash"]
    assert database_reads == []


def test_stable_first_identity_hash_remains_diagnostic_only(tmp_path):
    store, scope = _case(tmp_path)
    result = review.review_memory_revision_reuse(
        store, scope, "source", expected_revision=1,
    )
    assert result.live_revision == 1
    assert result.generation_count == 1
    assert result.generation_authenticated is False
    assert result.write_authorized is False
    assert result.erase_authorized is False
    assert "PRIVATE-FIXTURE" not in repr(result)
