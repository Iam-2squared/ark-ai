"""Row/event Memory audit is content-free and constructor-fenced.

No manual review can authenticate a writer, consent, clock or real erasure.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_event_alignment as alignment
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(MemoryScope("fixture-user"), "source", "private canary"))
    return store


def test_preinstalled_report_constructor_rejected_before_sqlite_read(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("hostile Memory audit constructor ran")

    with monkeypatch.context() as patch:
        patch.setattr(alignment.MemoryEventAlignmentReview, "__init__", hostile)
        patch.setattr(
            store, "_connect_readonly",
            lambda: pytest.fail("SQLite accessed after report class drift"),
        )
        with pytest.raises(
            alignment.MemoryEventAlignmentRejected, match="authority epoch changed",
        ):
            alignment.review_memory_event_alignment(store)
    assert invoked == []


@pytest.mark.parametrize("phase", ("row", "event"))
def test_constructor_changed_during_row_or_event_hash_never_invoked(
    tmp_path, monkeypatch, phase,
):
    store = _store(tmp_path)
    original = alignment._charge
    invoked = []

    def hostile(self, *args, **kwargs):
        invoked.append(True)
        raise AssertionError("substituted Memory audit initializer ran")

    def mutate(digest, entry):
        if entry[0] == phase:
            monkeypatch.setattr(alignment.MemoryEventAlignmentReview, "__init__", hostile)
        return original(digest, entry)

    with monkeypatch.context() as patch:
        patch.setattr(alignment, "_charge", mutate)
        with pytest.raises(
            alignment.MemoryEventAlignmentRejected, match="authority epoch changed",
        ):
            alignment.review_memory_event_alignment(store)
    assert invoked == []


def test_original_local_alignment_digest_does_not_reveal_content(tmp_path):
    store = _store(tmp_path)
    review = alignment.review_memory_event_alignment(store)
    assert review.row_count == review.event_count == 1
    assert review.last_event_id == 1
    assert len(review.digest) == 64
    assert "private canary" not in repr(review)
    assert review.independently_authenticated is False
    assert review.user_consent_verified is False
    assert review.deletion_or_erasure_proven is False
    assert review.action_authorized is False
