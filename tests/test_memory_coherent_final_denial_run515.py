"""Injected final denial getter must be refused before retained Memory reads."""

from __future__ import annotations

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_row_delta_review import capture_local_memory_row_delta


def _context(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "coherent-last-denial.sqlite3", clock_ms=lambda: 9000,
    )
    store.put(MemoryWrite(MemoryScope("owner", "notes"), "first", "private canary"))
    witnesses = (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
        capture_local_memory_row_delta(store),
    )
    return store, witnesses


def _verify(store, retained):
    return coherent.review_retained_coherent_memory(
        store, retained[0], retained[1], prior_rows=retained[2],
    )


def test_honest_coherent_read_is_stable_and_contains_no_private_text(tmp_path):
    store, retained = _context(tmp_path)
    first = _verify(store, retained)
    second = _verify(store, retained)
    assert first == second
    assert first.retained_row_delta_checked is True
    assert first.memory_disclosure_authorized is False
    assert first.action_authorized is False
    assert first.cross_store_atomicity_proven is False
    assert "private canary" not in repr(first)


@pytest.mark.parametrize("field,value", (
    ("review_sha256", "0" * 64),
    ("current_alignment_sha256", "0" * 64),
    ("current_event_sha256", "0" * 64),
    ("status", "FORGED_AUTHENTICATED"),
    ("retained_row_delta_checked", False),
    ("current_event_count", 0),
    ("row_count", 0),
    ("scope_count", 0),
    ("last_event_id", 0),
))
def test_last_false_denial_getter_cannot_rewrite_review(
    tmp_path, monkeypatch: pytest.MonkeyPatch, field: str, value: object,
):
    store, retained = _context(tmp_path)
    called = []

    def corrupt(self):
        called.append("injected")
        object.__setattr__(self, field, value)
        return False

    monkeypatch.setattr(
        coherent.RetainedCoherentMemoryReview,
        "cross_store_atomicity_proven",
        property(corrupt),
    )
    with pytest.raises(
        coherent.MemoryCoherentHistoryRejected,
        match="result constructor or authority descriptor changed",
    ):
        _verify(store, retained)
    assert called == []


def test_same_value_replaced_digest_carrier_is_still_detected(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
):
    store, retained = _context(tmp_path)
    called = []

    def change_carrier(self):
        called.append("injected")
        original = self.review_sha256
        replacement = ("_" + original)[1:]
        assert replacement == original and replacement is not original
        object.__setattr__(self, "review_sha256", replacement)
        return False

    monkeypatch.setattr(
        coherent.RetainedCoherentMemoryReview,
        "cross_store_atomicity_proven",
        property(change_carrier),
    )
    with pytest.raises(
        coherent.MemoryCoherentHistoryRejected,
        match="result constructor or authority descriptor changed",
    ):
        _verify(store, retained)
    assert called == []


def test_last_false_denial_getter_cannot_silently_hide_row_witness(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
):
    store, retained = _context(tmp_path)

    def hide_optional_row_audit(self):
        object.__setattr__(self, "retained_row_delta_checked", False)
        return False

    monkeypatch.setattr(
        coherent.RetainedCoherentMemoryReview,
        "cross_store_atomicity_proven",
        property(hide_optional_row_audit),
    )
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        _verify(store, retained)
