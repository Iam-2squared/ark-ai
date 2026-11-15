"""Late MappingProxyType backing-dict mutation must not reach epoch sorting.

Only caller-built synthetic MemoryRecords, never live user data or external tools.
"""

import hashlib
from types import MappingProxyType

import pytest

from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


def _snapshot() -> tuple[dict[str, str], CoherentSnapshotReview]:
    scope = MemoryScope("synthetic-owner", "local")
    source_id = "synthetic-source"
    payload = "private synthetic row"
    backing = {"tag": "ok"}
    record = MemoryRecord(
        deterministic_memory_id(scope, source_id),
        scope, source_id, payload, {}, 1, 2, None, 1,
        hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )
    object.__setattr__(record, "metadata", MappingProxyType(backing))
    return backing, CoherentSnapshotReview(
        10, (scope,), ((record,),), "a" * 64,
    )


@pytest.mark.parametrize("mutation", (
    "entry_count", "codepoint_width", "utf8_width", "invalid_unicode",
))
def test_reentrant_hash_cannot_sort_mutated_metadata(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    backing, snapshot = _snapshot()
    original_hash = context._hash
    original_sorted = sorted
    changed = [False]
    sorted_after_mutation: list[bool] = []

    def mutate_then_hash(label: str, payload: object) -> str:
        if not changed[0]:
            changed[0] = True
            if mutation == "entry_count":
                backing.update({f"extra{i}": "v" for i in range(65)})
            elif mutation == "codepoint_width":
                backing["tag"] = "x" * 4097
            elif mutation == "utf8_width":
                backing["tag"] = "🪐" * 1025
            else:
                backing["tag"] = "bad\ud800"
        return original_hash(label, payload)

    def observed_sorted(iterable: object, *args: object, **kwargs: object) -> object:
        if changed[0]:
            sorted_after_mutation.append(True)
        return original_sorted(iterable, *args, **kwargs)

    # Module-local replacement avoids changing Python's global builtins.
    with monkeypatch.context() as patch:
        patch.setattr(context, "_hash", mutate_then_hash)
        patch.setattr(context, "sorted", observed_sorted, raising=False)
        with pytest.raises(
            context.PersonalContextReviewRejected,
            match="context input changed during selection",
        ):
            context.review_personal_context(
                snapshot, context.ContextSelectionPolicy(1, 1),
            )
    assert changed == [True]
    assert sorted_after_mutation == []
