"""Bound reflected metadata UTF-8 before private Personal Context hashing.

Only synthetic, in-memory records. No live Personal Context, storage, network
or permission/dispatch integration. Frozen Memory v1 schema remains unchanged.
"""

import hashlib
import sys
from types import MappingProxyType

import pytest

from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


def _inputs(metadata: dict[str, str]) -> CoherentSnapshotReview:
    scope = MemoryScope("synthetic-owner", "private")
    source_id = "offline-fixture"
    content = "synthetic private payload"
    record = MemoryRecord(
        deterministic_memory_id(scope, source_id), scope, source_id,
        content, {}, 1, 2, None, 1,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )
    object.__setattr__(record, "metadata", MappingProxyType(metadata))
    return CoherentSnapshotReview(10, (scope,), ((record,),), "a" * 64)


@pytest.mark.parametrize(
    ("metadata", "error"),
    (
        ({"🪐" * 1025: "value"}, "metadata UTF-8 byte budget"),
        ({"key": "🪐" * 1025}, "metadata UTF-8 byte budget"),
        ({"é" * 2049: "value"}, "metadata UTF-8 byte budget"),
        ({"key": "é" * 2049}, "metadata UTF-8 byte budget"),
        ({"k\ud800": "value"}, "metadata is not valid UTF-8"),
        ({"key": "v\udfff"}, "metadata is not valid UTF-8"),
        ({"a": "safe", "key": "🪐" * 1025}, "metadata UTF-8 byte budget"),
        ({"a": "safe", "key": "v\ud800"}, "metadata is not valid UTF-8"),
    ),
)
def test_invalid_metadata_fails_before_sensitive_hash(
    metadata: dict[str, str], error: str,
) -> None:
    snapshot = _inputs(metadata)
    observed: list[object] = []
    previous = sys.getprofile()

    def profile(frame: object, event: str, arg: object) -> None:
        if (
            event == "c_call"
            and getattr(frame, "f_code", None)
            is context.review_personal_context.__code__
            and arg is hashlib.sha256
        ):
            observed.append(arg)

    sys.setprofile(profile)
    try:
        with pytest.raises(context.PersonalContextReviewRejected, match=error):
            context.review_personal_context(
                snapshot, context.ContextSelectionPolicy(1, 1),
            )
    finally:
        sys.setprofile(previous)
    assert observed == []


@pytest.mark.parametrize(
    "metadata",
    (
        {"🪐" * 1024: "value"},
        {"key": "🪐" * 1024},
        {"é" * 2048: "value"},
        {"key": "é" * 2048},
    ),
)
def test_exact_utf8_boundary_is_inert_and_non_authorizing(
    metadata: dict[str, str],
) -> None:
    bundle = context.review_personal_context(
        _inputs(metadata), context.ContextSelectionPolicy(1, 1),
    )
    assert len(bundle.items) == 1
    assert bundle.items[0].content == "synthetic private payload"
    assert bundle.action_authorized is False
    assert bundle.dispatch_authorized is False
