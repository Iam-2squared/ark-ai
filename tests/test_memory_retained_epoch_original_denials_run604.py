"""Read-only retained epoch comparisons reject substituted authority descriptors."""

from __future__ import annotations

import pytest

from ark.memory import retained_epoch_review as retained
from ark.memory.atomic_epoch_review import review_atomic_memory_epoch
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


class Counterfeit:
    def __init__(self, original, calls):
        self.original = original
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("getter executed")
        return self.original if instance is None else False


def _pair(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-epoch-static.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "fixture", "local secret"), expected_revision=0)
    return (
        review_atomic_memory_epoch(store, (scope,)),
        review_atomic_memory_epoch(store, (scope,)),
    )


@pytest.mark.parametrize("flag", retained._REVIEW_DENIAL_NAMES)
def test_counterfeit_retained_review_property_is_never_invoked(
    tmp_path, monkeypatch, flag,
):
    previous, current = _pair(tmp_path)
    calls = []
    original = vars(retained._REVIEW_TYPE)[flag]
    monkeypatch.setattr(
        retained._REVIEW_TYPE, flag, Counterfeit(original, calls),
    )
    with pytest.raises(MemorySchemaError, match="authority descriptor changed"):
        retained.review_retained_memory_epoch(previous, current)
    assert calls == []


@pytest.mark.parametrize("flag", retained._COMPARISON_DENIAL_NAMES)
def test_late_counterfeit_result_property_is_never_invoked(
    tmp_path, monkeypatch, flag,
):
    previous, current = _pair(tmp_path)
    calls = []
    report_type = retained._COMPARISON_TYPE
    original = vars(report_type)[flag]

    def counterfeit_constructor(*args):
        result = report_type(*args)
        monkeypatch.setattr(report_type, flag, Counterfeit(original, calls))
        return result

    monkeypatch.setattr(
        retained, "RetainedMemoryEpochComparison", counterfeit_constructor,
    )
    with pytest.raises(MemorySchemaError, match="authority descriptor changed"):
        retained.review_retained_memory_epoch(previous, current)
    assert calls == []


def test_unchanged_epoch_retains_no_dispatch_or_provenance(tmp_path):
    previous, current = _pair(tmp_path)
    report = retained.review_retained_memory_epoch(previous, current)
    assert report.status == "UNCHANGED_LOCAL_CONTENT"
    assert report.new_event_counts == (0,)
    assert report.historical_prefix_proven is False
    assert report.independent_writer_proven is False
    assert report.custody_authenticated is False
    assert report.memory_disclosure_authorized is False
    assert report.dispatch_authorized is False
