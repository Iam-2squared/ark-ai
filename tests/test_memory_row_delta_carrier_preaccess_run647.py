"""Retained Memory row delta does not execute poisoned carrier descriptors.

Local SQLite only; this neither authenticates historical writers nor authorizes
private-memory disclosure or any action.
"""

from __future__ import annotations

import pytest

import ark.memory.sqlite_retained_row_delta_review as delta
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-row-custody.sqlite3", clock_ms=lambda: 2000,
    )
    store.put(
        MemoryWrite(MemoryScope("owner", "private"), "note", "秘密 fixture"),
    )
    return store, delta.capture_local_memory_row_delta(store)


@pytest.mark.parametrize(
    "field", ("event_count", "last_event_id", "event_prefix_sha256", "rows"),
)
def test_poisoned_retained_witness_denied_before_scan(
    tmp_path, monkeypatch, field,
):
    store, retained = _fixture(tmp_path)
    invoked = []

    def hostile_getter(_self):
        invoked.append(field)
        raise AssertionError("private witness field was invoked")

    with monkeypatch.context() as patch:
        patch.setattr(
            delta.MemoryRowDeltaWitness, field, property(hostile_getter),
        )
        patch.setattr(
            delta, "_scan",
            lambda _store: pytest.fail("memory scan began before witness veto"),
        )
        with pytest.raises(
            delta.MemoryRowDeltaRejected, match="carrier descriptors changed",
        ):
            delta.review_retained_memory_row_delta(store, retained)
    assert invoked == []


@pytest.mark.parametrize(
    "field", (
        "retained_rows", "current_rows", "appended_events",
        "explained_changes", "review_sha256",
    ),
)
def test_poisoned_report_field_denied_before_private_scan(
    tmp_path, monkeypatch, field,
):
    store, _ = _fixture(tmp_path)
    invoked = []

    def hostile_getter(_self):
        invoked.append(field)
        raise AssertionError("private report field was invoked")

    with monkeypatch.context() as patch:
        patch.setattr(
            delta.MemoryRowDeltaReview, field, property(hostile_getter),
        )
        patch.setattr(
            delta, "_scan",
            lambda _store: pytest.fail("memory scan began before report veto"),
        )
        with pytest.raises(
            delta.MemoryRowDeltaRejected, match="carrier descriptors changed",
        ):
            delta.capture_local_memory_row_delta(store)
    assert invoked == []


@pytest.mark.parametrize("carrier", ("witness", "report"))
@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_poisoned_lookup_hook_denied_before_private_scan(
    tmp_path, monkeypatch, carrier, hook,
):
    store, retained = _fixture(tmp_path)
    invoked = []
    target = (
        delta.MemoryRowDeltaWitness
        if carrier == "witness" else delta.MemoryRowDeltaReview
    )

    def hostile_lookup(_self, _name):
        invoked.append((carrier, hook))
        raise AssertionError("injected lookup executed")

    with monkeypatch.context() as patch:
        patch.setattr(target, hook, hostile_lookup, raising=False)
        patch.setattr(
            delta, "_scan",
            lambda _store: pytest.fail("memory scan began before hook veto"),
        )
        with pytest.raises(
            delta.MemoryRowDeltaRejected, match="carrier descriptors changed",
        ):
            delta.review_retained_memory_row_delta(store, retained)
    assert invoked == []


def test_late_scan_callback_cannot_rebind_result_field(
    tmp_path, monkeypatch,
):
    store, retained = _fixture(tmp_path)
    original = delta._scan
    invoked = []

    def poisoned_field(_self):
        invoked.append(True)
        raise AssertionError("late report slot invoked")

    def inject_after_scan(source):
        result = original(source)
        monkeypatch.setattr(
            delta.MemoryRowDeltaReview, "review_sha256", property(poisoned_field),
        )
        return result

    with monkeypatch.context() as patch:
        patch.setattr(delta, "_scan", inject_after_scan)
        with pytest.raises(
            delta.MemoryRowDeltaRejected, match="carrier descriptors changed",
        ):
            delta.review_retained_memory_row_delta(store, retained)
    assert invoked == []


def test_valid_row_delta_remains_content_free_and_inert(tmp_path):
    store, retained = _fixture(tmp_path)
    store.put(
        MemoryWrite(MemoryScope("owner", "private"), "other", "追加記録"),
    )
    report = delta.review_retained_memory_row_delta(store, retained)
    assert report.appended_events == 1
    assert report.explained_changes == 1
    assert report.writer_authenticated is False
    assert report.disclosure_authorized is False
    assert report.action_authorized is False
    assert "秘密 fixture" not in repr(retained)
    assert "追加記録" not in repr(report)
