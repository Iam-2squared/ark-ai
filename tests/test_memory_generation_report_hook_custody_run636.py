"""Guard inert Memory-generation report construction across callbacks.

No Memory v1 schema, CAS write semantics or private content is altered.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as review


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("only-local", "diagnostics")
    store.put(MemoryWrite(scope, "item", "private"), expected_revision=0)
    return store, scope


def _review(state):
    store, scope = state
    return review.review_memory_revision_reuse(
        store, scope, "item", expected_revision=1,
    )


@pytest.mark.parametrize(
    "changed",
    ("constructor", "field", "denial", "lookup_hook"),
)
def test_report_reflection_is_refused_before_private_sqlite_scan(
    tmp_path, monkeypatch, changed,
):
    state = _case(tmp_path)
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("executed")
        raise AssertionError("forged report hook executed")

    klass = review.MemoryGenerationReview
    if changed == "constructor":
        monkeypatch.setattr(klass, "__init__", forbidden)
    elif changed == "field":
        monkeypatch.setattr(klass, "memory_id", property(forbidden))
    elif changed == "denial":
        monkeypatch.setattr(klass, "write_authorized", property(forbidden))
    else:
        monkeypatch.setattr(klass, "__getattribute__", forbidden)

    with pytest.raises(
        review.MemoryGenerationReviewRejected,
        match="report constructor or authority changed",
    ):
        _review(state)
    assert calls == []


def test_row_hydration_cannot_swap_report_constructor_before_result(
    tmp_path, monkeypatch,
):
    state = _case(tmp_path)
    native_record = review._record
    called = []

    def forged_init(*_args, **_kwargs):
        called.append("forged")
        raise AssertionError("executed forged constructor")

    def hydrate_then_rebind(row):
        result = native_record(row)
        monkeypatch.setattr(review.MemoryGenerationReview, "__init__", forged_init)
        return result

    monkeypatch.setattr(review, "_record", hydrate_then_rebind)
    with pytest.raises(
        review.MemoryGenerationReviewRejected,
        match="report constructor or authority changed",
    ):
        _review(state)
    assert called == []


def test_normal_generation_report_remains_advisory_only(tmp_path):
    report = _review(_case(tmp_path))
    assert report.generation_count == 1
    assert report.live_revision == 1
    assert report.revision_reuse_possible is False
    assert report.write_authorized is False
    assert report.erase_authorized is False
    assert report.generation_authenticated is False
