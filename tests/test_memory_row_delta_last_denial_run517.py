"""Retained Memory row report is inert even after its final denial getter.

All rows and local witnesses are synthetic; no private text is disclosed or
deleted, and no report can authorize an action or prove past writer identity.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.memory.sqlite_retained_row_delta_review as delta
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("mutation", (
    "digest", "equal_digest", "count_bool", "earlier_authority",
))
def test_last_denial_getter_cannot_rewrite_memory_row_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1500)
    store.put(
        MemoryWrite(MemoryScope("owner", "notes"), "source", "fixture only"),
        expected_revision=0,
    )
    retained = delta.capture_local_memory_row_delta(store)
    calls = 0

    def mutate_and_deny(report: delta.MemoryRowDeltaReview) -> bool:
        nonlocal calls
        calls += 1
        if mutation == "digest":
            object.__setattr__(report, "review_sha256", "f" * 64)
        elif mutation == "equal_digest":
            old = report.review_sha256
            copied = ("_" + old)[1:]
            assert old == copied and old is not copied
            object.__setattr__(report, "review_sha256", copied)
        elif mutation == "count_bool":
            object.__setattr__(report, "current_rows", True)
        else:
            monkeypatch.setattr(
                delta.MemoryRowDeltaReview,
                "writer_authenticated",
                property(lambda _self: True),
            )
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            delta.MemoryRowDeltaReview,
            "action_authorized",
            property(mutate_and_deny),
        )
        with pytest.raises(delta.MemoryRowDeltaRejected, match="changed|authority"):
            delta.review_retained_memory_row_delta(store, retained)
    assert calls >= 1


def test_stable_row_delta_review_remains_non_authorizing(tmp_path: Path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1500)
    retained = delta.capture_local_memory_row_delta(store)
    report = delta.review_retained_memory_row_delta(store, retained)
    assert report.retained_rows == report.current_rows == 0
    assert report.writer_authenticated is False
    assert report.disclosure_authorized is False
    assert report.action_authorized is False
