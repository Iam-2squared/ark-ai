"""Local Memory alignment receipts retain original deny-only authority.

No external consent, independent custody, model or backend action is involved.
"""

import pytest

import ark.memory.sqlite_event_alignment as alignment
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    MemoryEventAlignmentReview,
    review_memory_event_alignment,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(MemoryScope("local-user"), "fixture", "synthetic"))
    return store


@pytest.mark.parametrize(
    "name",
    (
        "independently_authenticated",
        "user_consent_verified",
        "deletion_or_erasure_proven",
        "action_authorized",
    ),
)
def test_equal_false_descriptor_replacement_cannot_reauthorize_review(
    tmp_path, monkeypatch, name,
):
    store = _store(tmp_path)
    monkeypatch.setattr(MemoryEventAlignmentReview, name, property(lambda self: False))
    with pytest.raises(MemoryEventAlignmentRejected, match="authority epoch"):
        review_memory_event_alignment(store)


def test_reentrant_equal_false_descriptor_replacement_is_detected(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    original_charge = alignment._charge

    def reentrant_charge(digest, entry):
        if entry[0] == "event":
            monkeypatch.setattr(
                MemoryEventAlignmentReview,
                "action_authorized",
                property(lambda self: False),
            )
        return original_charge(digest, entry)

    monkeypatch.setattr(alignment, "_charge", reentrant_charge)
    with pytest.raises(MemoryEventAlignmentRejected, match="authority epoch"):
        review_memory_event_alignment(store)


def test_unchanged_review_remains_digest_only_and_deny_only(tmp_path):
    reviewed = review_memory_event_alignment(_store(tmp_path))
    assert (reviewed.row_count, reviewed.event_count, reviewed.last_event_id) == (1, 1, 1)
    assert len(reviewed.digest) == 64
    assert reviewed.independently_authenticated is False
    assert reviewed.user_consent_verified is False
    assert reviewed.deletion_or_erasure_proven is False
    assert reviewed.action_authorized is False
