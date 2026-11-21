"""Bound reflected Memory metadata before private Personal Context projection.

Inert, caller-built Memory records; no live account, storage or tool access.
"""

import hashlib
import sys
from types import MappingProxyType

import pytest

from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


def _inputs() -> tuple[MemoryRecord, CoherentSnapshotReview]:
    scope = MemoryScope("synthetic-owner", "local")
    source = "fixture-key"
    record = MemoryRecord(
        deterministic_memory_id(scope, source),
        scope, source, "synthetic private row", {"valid": "metadata"},
        1, 2, None, 1,
        hashlib.sha256(b"synthetic private row").hexdigest(),
    )
    snapshot = CoherentSnapshotReview(
        10, (scope,), ((record,),), "a" * 64,
    )
    return record, snapshot


class HiddenCallback(dict[str, str]):
    def items(self) -> object:  # type: ignore[override]
        raise AssertionError("noncanonical mapping callback executed")


class StrSubclass(str):
    pass


@pytest.mark.parametrize(
    "bad",
    (
        {},
        {str(i): "v" for i in range(65)},
        {"x" * 4097: "value"},
        {"key": "x" * 4097},
        {1: "value"},
        {"key": 1},
        {StrSubclass("key"): "value"},
        {"key": StrSubclass("value")},
        HiddenCallback({"key": "private"}),
    ),
)
def test_reflected_metadata_denied_before_private_row_hash(
    bad: object,
) -> None:
    record, snapshot = _inputs()
    object.__setattr__(record, "metadata", bad)
    calls: list[object] = []
    previous = sys.getprofile()

    def profile(frame: object, event: str, arg: object) -> None:
        if (
            event == "c_call"
            and getattr(frame, "f_code", None)
            is context.review_personal_context.__code__
            and arg is hashlib.sha256
        ):
            calls.append(arg)

    sys.setprofile(profile)
    try:
        with pytest.raises(
            context.PersonalContextReviewRejected,
            match="metadata shape/budget",
        ):
            context.review_personal_context(
                snapshot, context.ContextSelectionPolicy(1, 1),
            )
    finally:
        sys.setprofile(previous)
    assert calls == []


def test_bounded_metadata_mapping_still_yields_inert_context() -> None:
    record, snapshot = _inputs()
    object.__setattr__(
        record, "metadata", MappingProxyType({"k" * 4096: "v" * 4096}),
    )
    projected = context.review_personal_context(
        snapshot, context.ContextSelectionPolicy(1, 1),
    )
    assert len(projected.items) == 1
    assert projected.items[0].content == "synthetic private row"
    assert projected.dispatch_authorized is False
    assert projected.action_authorized is False
