"""Retained Memory comparison refuses changed constructors before evaluating them.

This is read-only, local SQLite consistency evidence; no approval, custody,
content disclosure, or automatic retry is inferred from the comparison.
"""

import pytest

import ark.memory.sqlite_alignment_retained_review as compare
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "retained.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(MemoryScope("fixture-owner"), "source", "private-fixture"))
    return store, review_memory_event_alignment(store)


@pytest.mark.parametrize("moment", ("preinstalled", "after_alignment", "after_encoding"))
def test_changed_result_initializer_is_never_executed(
    tmp_path, monkeypatch, moment,
):
    store, retained = _fixture(tmp_path)
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("untrusted constructor called")
        raise AssertionError("forged result constructor must not execute")

    with monkeypatch.context() as patch:
        if moment == "preinstalled":
            patch.setattr(compare.RetainedMemoryAlignmentComparison, "__init__", forbidden)

            def no_sqlite():
                raise AssertionError("should reject before SQLite reads")

            patch.setattr(store, "_connect_readonly", no_sqlite)
        elif moment == "after_alignment":
            native = compare.review_memory_event_alignment

            def after_alignment(source):
                result = native(source)
                patch.setattr(
                    compare.RetainedMemoryAlignmentComparison, "__init__", forbidden,
                )
                return result

            patch.setattr(compare, "review_memory_event_alignment", after_alignment)
        else:
            native = compare.json.dumps

            def after_encoding(value, *args, **kwargs):
                encoded = native(value, *args, **kwargs)
                if (
                    type(value) is tuple and len(value) == 3
                    and value[-1] == "UNCHANGED_LOCAL_HISTORY"
                ):
                    patch.setattr(
                        compare.RetainedMemoryAlignmentComparison, "__init__", forbidden,
                    )
                return encoded

            patch.setattr(compare.json, "dumps", after_encoding)

        with pytest.raises(
            compare.MemoryAlignmentHistoryRejected, match="authority descriptor",
        ):
            compare.compare_retained_memory_alignment(store, retained)

    assert attempted == []
    # Rejected diagnostic does not alter the persisted event/row snapshot.
    report = compare.compare_retained_memory_alignment(store, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.appended_event_count == 0


def test_rebound_result_class_is_refused_before_sqlite(tmp_path, monkeypatch):
    store, retained = _fixture(tmp_path)
    original = compare.RetainedMemoryAlignmentComparison

    class Counterfeit(original):
        pass

    with monkeypatch.context() as patch:
        patch.setattr(compare, "RetainedMemoryAlignmentComparison", Counterfeit)

        def no_sqlite():
            raise AssertionError("result class changed before SQLite")

        patch.setattr(store, "_connect_readonly", no_sqlite)
        with pytest.raises(
            compare.MemoryAlignmentHistoryRejected, match="authority descriptor",
        ):
            compare.compare_retained_memory_alignment(store, retained)


def test_unchanged_result_never_grants_disclosure_or_dispatch(tmp_path):
    store, retained = _fixture(tmp_path)
    review = compare.compare_retained_memory_alignment(store, retained)
    assert review.previous_event_count == 1
    assert review.current_event_count == 1
    assert review.appended_event_count == 0
    assert review.historical_prefix_authenticated is False
    assert review.writer_authenticated is False
    assert review.content_disclosure_authorized is False
    assert review.dispatch_authorized is False
    assert "private-fixture" not in repr(review)
