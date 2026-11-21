"""Retained Memory history reviews never evaluate forged authority getters.

Local read-only evidence is not human consent, secure deletion or provenance.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_alignment_retained_review as compare
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentReview,
    review_memory_event_alignment,
)
from ark.memory.sqlite_store import SQLiteMemoryStore

_FLAGS = (
    *((MemoryEventAlignmentReview, name) for name in (
        "independently_authenticated", "user_consent_verified",
        "deletion_or_erasure_proven", "action_authorized",
    )),
    *((compare.RetainedMemoryAlignmentComparison, name) for name in (
        "historical_prefix_authenticated", "writer_authenticated",
        "content_disclosure_authorized", "dispatch_authorized",
    )),
)


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "local-memory.sqlite", clock_ms=lambda: 10)
    store.put(MemoryWrite(MemoryScope("owner"), "fixture", "private"))
    retained = review_memory_event_alignment(store)
    return store, retained


@pytest.mark.parametrize(("owner", "field"), _FLAGS)
@pytest.mark.parametrize("moment", ("before_review", "during_alignment"))
def test_original_false_authority_descriptors_required_without_getter(
    tmp_path, monkeypatch, owner, field, moment,
):
    store, retained = _fixture(tmp_path)
    calls: list[int] = []

    class Counterfeit:
        def __get__(self, _instance, _owner=None):
            calls.append(1)
            return False

    fake = Counterfeit()
    if moment == "before_review":
        monkeypatch.setattr(owner, field, fake)
    else:
        original = compare.review_memory_event_alignment

        def inject(source):
            result = original(source)
            monkeypatch.setattr(owner, field, fake)
            return result

        monkeypatch.setattr(compare, "review_memory_event_alignment", inject)

    with pytest.raises(compare.MemoryAlignmentHistoryRejected, match="authority"):
        compare.compare_retained_memory_alignment(store, retained)
    assert calls == []


def test_normal_local_comparison_stays_nonauthorizing(tmp_path):
    store, retained = _fixture(tmp_path)
    report = compare.compare_retained_memory_alignment(store, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.historical_prefix_authenticated is False
    assert report.writer_authenticated is False
    assert report.content_disclosure_authorized is False
    assert report.dispatch_authorized is False
