"""Retained coherent Memory review rejects executable result substitutions.

Local SQLite-only fixture: neither hashes nor result flags authenticate a
writer, an event time, consent, disclosure rights or external side effects.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_retained_coherent_review as coherent
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "coherent-result.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    saved = store.put(MemoryWrite(scope, "source", "private fixture content"))
    retained = (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
    )
    return store, saved, retained


@pytest.mark.parametrize(
    "replacement", ("result-class", "constructor", "field", "last-denial"),
)
def test_preinstalled_result_code_never_executes_before_private_read(
    tmp_path, monkeypatch, replacement,
):
    store, saved, retained = _fixture(tmp_path)
    calls = []

    def unsafe(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("injected executable report code ran")

    if replacement == "result-class":
        class FakeReview:
            def __init__(self, *args):
                unsafe(*args)

        monkeypatch.setattr(coherent, "RetainedCoherentMemoryReview", FakeReview)
    elif replacement == "constructor":
        monkeypatch.setattr(coherent.RetainedCoherentMemoryReview, "__init__", unsafe)
    elif replacement == "field":
        monkeypatch.setattr(
            coherent.RetainedCoherentMemoryReview,
            "status", property(unsafe),
        )
    else:
        monkeypatch.setattr(
            coherent.RetainedCoherentMemoryReview,
            "cross_store_atomicity_proven", property(unsafe),
        )

    with pytest.raises(
        coherent.MemoryCoherentHistoryRejected,
        match="result constructor or authority descriptor changed",
    ):
        coherent.review_retained_coherent_memory(store, *retained)
    assert calls == []
    assert store.get(saved.memory_id, saved.scope).content == "private fixture content"


def test_hash_callback_cannot_replace_report_constructor_before_use(
    tmp_path, monkeypatch,
):
    store, saved, retained = _fixture(tmp_path)
    real_hash = coherent.hashlib.sha256
    calls = []
    attempted = []

    def unsafe_init(*args):
        calls.append(args)
        raise AssertionError("injected constructor executed")

    def mutate_after_result_hash(payload=b""):
        if payload.startswith(coherent._RESULT_DOMAIN):
            attempted.append("digest")
            monkeypatch.setattr(
                coherent.RetainedCoherentMemoryReview, "__init__", unsafe_init,
            )
        return real_hash(payload)

    monkeypatch.setattr(coherent.hashlib, "sha256", mutate_after_result_hash)
    # The new alignment SHA preaccess guard refuses the rebound callback
    # while validating the retained witness, BEFORE private SQLite or the
    # coherent result hash can reach the injected constructor mutation.
    with pytest.raises(
        coherent.MemoryCoherentHistoryRejected,
        match="coherent Memory digest implementation or domain changed",
    ):
        coherent.review_retained_coherent_memory(store, *retained)
    assert attempted == []
    assert calls == []
    assert store.get(saved.memory_id, saved.scope).revision == 1


def test_original_review_still_returns_inert_coherent_event_and_row_snapshot(tmp_path):
    store, saved, retained = _fixture(tmp_path)
    result = coherent.review_retained_coherent_memory(store, *retained)
    assert result.current_event_count == 1
    assert result.row_count == 1
    assert result.current_alignment_sha256 == retained[1].digest
    assert result.current_event_sha256 == retained[0].prefix_sha256
    assert result.independently_authenticated is False
    assert result.historical_writer_authenticated is False
    assert result.consent_verified is False
    assert result.memory_disclosure_authorized is False
    assert result.action_authorized is False
    assert result.cross_store_atomicity_proven is False
    assert store.get(saved.memory_id, saved.scope).revision == 1
