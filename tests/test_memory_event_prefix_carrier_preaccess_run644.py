"""Local event-prefix carrier fields cannot execute forged descriptors.

Read-only, disposable SQLite; witnesses never identify a writer, authorize
memory disclosure, or authorize retries. Tests replace only class-local
dataclass fields and restore them through pytest's monkeypatch fixture.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_prefix_review as prefix


def _local_fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "prefix-carrier.sqlite", clock_ms=lambda: 1000,
    )
    store.put(MemoryWrite(MemoryScope("owner", "private"), "key", "secret"))
    return store, prefix.capture_local_memory_event_prefix(store)


@pytest.mark.parametrize(
    "field", ("event_count", "last_event_id", "prefix_sha256"),
)
def test_retained_witness_field_rebound_denied_before_scan(
    tmp_path, monkeypatch, field,
):
    store, retained = _local_fixture(tmp_path)
    invoked = []

    def malicious_read(_self):
        invoked.append(field)
        raise AssertionError("injected witness descriptor read")

    def forbidden_scan(*_args, **_kwargs):
        raise AssertionError("retained witness should be rejected before DB scan")

    monkeypatch.setattr(
        prefix.MemoryEventPrefixWitness, field, property(malicious_read),
    )
    monkeypatch.setattr(prefix, "_scan", forbidden_scan)
    with pytest.raises(
        prefix.MemoryEventPrefixRejected,
        match="retained event witness authority changed",
    ):
        prefix.compare_local_memory_event_prefix(store, retained)
    assert invoked == []


@pytest.mark.parametrize(
    "field", (
        "previous_event_count", "current_event_count",
        "status", "comparison_sha256",
    ),
)
def test_comparison_field_rebound_denied_before_result_construction(
    tmp_path, monkeypatch, field,
):
    store, retained = _local_fixture(tmp_path)
    invoked = []

    def malicious_read(_self):
        invoked.append(field)
        raise AssertionError("injected comparison descriptor read")

    monkeypatch.setattr(
        prefix.MemoryEventPrefixComparison, field, property(malicious_read),
    )
    with pytest.raises(
        prefix.MemoryEventPrefixRejected,
        match="event prefix comparison authority changed",
    ):
        prefix.compare_local_memory_event_prefix(store, retained)
    assert invoked == []


def test_comparison_digest_callback_cannot_replace_result_slot(
    tmp_path, monkeypatch,
):
    store, retained = _local_fixture(tmp_path)
    invoked = []
    original_sha256 = prefix.hashlib.sha256

    def malicious_read(_self):
        invoked.append("status")
        raise AssertionError("injected comparison status descriptor")

    def inject_on_digest(data=b""):
        if data.startswith(prefix._COMPARISON_DOMAIN):
            monkeypatch.setattr(
                prefix.MemoryEventPrefixComparison,
                "status",
                property(malicious_read),
            )
        return original_sha256(data)

    monkeypatch.setattr(prefix.hashlib, "sha256", inject_on_digest)
    with pytest.raises(
        prefix.MemoryEventPrefixRejected,
        match="event prefix comparison authority changed",
    ):
        prefix.compare_local_memory_event_prefix(store, retained)
    assert invoked == []


def test_original_event_prefix_carriers_remain_read_only_and_denied(tmp_path):
    store, retained = _local_fixture(tmp_path)
    store.put(MemoryWrite(MemoryScope("owner", "private"), "other", "追加"))
    report = prefix.compare_local_memory_event_prefix(store, retained)
    assert report.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert report.current_event_count == retained.event_count + 1
    assert retained.historical_writer_authenticated is False
    assert report.historical_writer_authenticated is False
    assert report.independent_witness_custody_proven is False
    assert report.action_authorized is False
