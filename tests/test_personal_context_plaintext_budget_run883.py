"""Content-bounded ephemeral Personal Context over synthetic Memory rows.

No live account, user profile, persistent plaintext write, retrieval API,
external tool, model or trusted-clock provider is involved.
"""

import hashlib

import pytest

from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


def _record(scope: MemoryScope, number: int, content: str) -> MemoryRecord:
    source_id = f"synthetic-{number}"
    return MemoryRecord(
        deterministic_memory_id(scope, source_id), scope, source_id,
        content, {}, 1, 2, None, 1,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def _snapshot(*records: MemoryRecord) -> CoherentSnapshotReview:
    scope = MemoryScope("fixture-owner", "private")
    return CoherentSnapshotReview(
        100, (scope,), (tuple(records),), "a" * 64,
    )


@pytest.mark.parametrize(
    ("content", "message"),
    (
        ("x" * 65_537, "item budget"),
        ("é" * 32_769, "input budget"),
    ),
)
def test_private_plaintext_is_bounded_before_projection(
    content: str, message: str,
) -> None:
    scope = MemoryScope("fixture-owner", "private")
    record = _record(scope, 1, content)
    with pytest.raises(context.PersonalContextReviewRejected, match=message):
        context.review_personal_context(
            _snapshot(record), context.ContextSelectionPolicy(1, 1),
        )


def test_unpaired_surrogate_is_refused_before_hash() -> None:
    scope = MemoryScope("fixture-owner", "private")
    source = "invalid\ud800"
    record = MemoryRecord(
        deterministic_memory_id(scope, "synthetic-1"), scope,
        "synthetic-1", source, {}, 1, 2, None, 1, "a" * 64,
    )
    with pytest.raises(
        context.PersonalContextReviewRejected, match="not valid UTF-8",
    ):
        context.review_personal_context(
            _snapshot(record), context.ContextSelectionPolicy(1, 1),
        )


def test_total_scanned_plaintext_budget_prevents_unselected_input_bloat() -> None:
    scope = MemoryScope("fixture-owner", "private")
    rows = tuple(_record(scope, number, "z" * 65_536) for number in range(17))
    with pytest.raises(context.PersonalContextReviewRejected, match="input budget"):
        context.review_personal_context(
            _snapshot(*rows), context.ContextSelectionPolicy(1, 1),
        )


def test_exact_single_record_byte_budget_remains_non_authorizing() -> None:
    scope = MemoryScope("fixture-owner", "private")
    record = _record(scope, 1, "é" * 32_768)
    result = context.review_personal_context(
        _snapshot(record), context.ContextSelectionPolicy(1, 1),
    )
    assert len(result.items) == 1
    assert result.items[0].content == record.content
    assert result.action_authorized is False
    assert result.dispatch_authorized is False


def test_reflected_budget_override_is_refused_without_reinterpreting_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scope = MemoryScope("fixture-owner", "private")
    record = _record(scope, 1, "synthetic")
    monkeypatch.setattr(context, "_MAX_CONTEXT_ITEM_BYTES", 10_000_000)
    with pytest.raises(context.PersonalContextReviewRejected, match="budget changed"):
        context.review_personal_context(
            _snapshot(record), context.ContextSelectionPolicy(1, 1),
        )
