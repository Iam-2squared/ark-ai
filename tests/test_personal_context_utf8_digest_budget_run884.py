"""Detached Personal Context metadata admission; synthetic Memory only.

No live context, user identity, consent, network, tools or persistent plaintext.
"""

import hashlib
import re

import pytest

from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


@pytest.mark.parametrize(
    ("revision", "accepted"),
    (
        ("a" * 128, True),
        ("🪐" * 32, True),
        ("é" * 64, True),
        ("🪐" * 33, False),
        ("é" * 65, False),
    ),
)
def test_policy_revision_is_bounded_in_utf8_bytes(
    revision: str, accepted: bool,
) -> None:
    if accepted:
        policy = context.ContextSelectionPolicy(1, 1, revision)
        assert policy.policy_revision == revision
    else:
        with pytest.raises(ValueError, match="UTF-8 byte budget"):
            context.ContextSelectionPolicy(1, 1, revision)


def test_policy_surrogate_refused_before_private_snapshot_read() -> None:
    with pytest.raises(ValueError, match="not UTF-8"):
        context.ContextSelectionPolicy(1, 1, "offline\ud800")


def _snapshot(*, provenance: str = "a" * 64, row_hash: str = "") -> CoherentSnapshotReview:
    scope = MemoryScope("synthetic-owner", "local")
    text = "synthetic privacy data"
    record = MemoryRecord(
        deterministic_memory_id(scope, "synthetic-key"), scope,
        "synthetic-key", text, {}, 1, 2, None, 1,
        row_hash or hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
    return CoherentSnapshotReview(100, (scope,), ((record,),), provenance)


def test_oversized_snapshot_digest_refused_before_matcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExactMatcher:
        def fullmatch(self, value: str) -> object:
            assert len(value) == 64, "unbounded snapshot digest reached regex"
            return re.fullmatch(r"[0-9a-f]{64}", value)

    monkeypatch.setattr(context, "_HEX", ExactMatcher())
    with pytest.raises(context.PersonalContextReviewRejected, match="snapshot shape"):
        context.review_personal_context(
            _snapshot(provenance="a" * 65_536),
            context.ContextSelectionPolicy(1, 1),
        )


def test_oversized_record_digest_refused_before_matcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inspected: list[int] = []

    class ExactMatcher:
        def fullmatch(self, value: str) -> object:
            inspected.append(len(value))
            assert len(value) == 64, "unbounded record digest reached regex"
            return re.fullmatch(r"[0-9a-f]{64}", value)

    monkeypatch.setattr(context, "_HEX", ExactMatcher())
    with pytest.raises(context.PersonalContextReviewRejected, match="integrity/freshness"):
        context.review_personal_context(
            _snapshot(row_hash="a" * 65_536),
            context.ContextSelectionPolicy(1, 1),
        )
    assert inspected == [64]


def test_bounded_multibyte_policy_projection_is_inert() -> None:
    projected = context.review_personal_context(
        _snapshot(), context.ContextSelectionPolicy(1, 1, "🪐" * 32),
    )
    assert len(projected.items) == 1
    assert projected.action_authorized is False
    assert projected.dispatch_authorized is False
