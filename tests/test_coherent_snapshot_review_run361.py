"""Synthetic multi-namespace Memory read-snapshot integration regression tests."""

import sqlite3

import pytest

from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _setup(tmp_path):
    path = tmp_path / "snapshot.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope_a = MemoryScope("fixture-owner", "a")
    scope_b = MemoryScope("fixture-owner", "b")
    first = store.put(MemoryWrite(scope_a, "source-a", "first record"))
    second = store.put(MemoryWrite(scope_b, "source-b", "second record"))
    store.put(MemoryWrite(MemoryScope("other-owner", "a"), "private", "other secret"))
    return store, scope_a, scope_b, first, second


def test_scope_order_and_owner_isolation(tmp_path):
    store, scope_a, scope_b, first, second = _setup(tmp_path)
    req = CoherentSnapshotRequest("fixture-owner", ("b", "a"))
    review = review_coherent_snapshot(store, req)
    assert review.scopes == (scope_b, scope_a)
    assert [row.memory_id for row in review.records[0]] == [second.memory_id]
    assert [row.memory_id for row in review.records[1]] == [first.memory_id]
    assert all(row.scope.owner_id == "fixture-owner" for group in review.records for row in group)
    assert len(review.provenance_sha256) == 64
    assert "first record" not in review.provenance_sha256


@pytest.mark.parametrize(
    "namespaces",
    [
        (),
        ("a", "a"),
        tuple(str(i) for i in range(17)),
        ["a", "b"],
    ],
)
def test_invalid_namespace_sets_fail_closed(namespaces):
    with pytest.raises((TypeError, ValueError)):
        CoherentSnapshotRequest("fixture-owner", namespaces)


def test_expiry_uses_one_validated_time_for_all_namespaces(tmp_path):
    store, scope_a, scope_b, _, _ = _setup(tmp_path)
    store.put(MemoryWrite(scope_a, "expiry-a", "expires-a", expires_at_ms=120))
    store.put(MemoryWrite(scope_b, "expiry-b", "expires-b", expires_at_ms=120))
    samples = []

    def clock():
        samples.append(120)
        return 120

    store._clock_ms = clock
    req = CoherentSnapshotRequest("fixture-owner", ("a", "b"))
    result = review_coherent_snapshot(store, req)
    assert samples == [120]
    assert all(
        all(not record.content.startswith("expires-") for record in group)
        for group in result.records
    )
    with_expired = review_coherent_snapshot(
        store, CoherentSnapshotRequest("fixture-owner", ("a", "b"), include_expired=True)
    )
    assert [len(group) for group in with_expired.records] == [2, 2]


def test_corrupt_eligible_row_fails_whole_bundle(tmp_path):
    store, _, scope_b, _, second = _setup(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memories SET content_sha256=? WHERE memory_id=?",
            ("0" * 64, second.memory_id),
        )
    with pytest.raises(MemorySchemaError, match="digest"):
        review_coherent_snapshot(
            store, CoherentSnapshotRequest("fixture-owner", ("a", "b"))
        )


def test_writer_after_first_snapshot_read_cannot_mix_namespace_versions(tmp_path):
    store, scope_a, scope_b, first, second = _setup(tmp_path)
    writer = SQLiteMemoryStore(store.path, clock_ms=lambda: 101)
    seen = []

    def write_during_clock():
        seen.append("writer")
        writer.put(MemoryWrite(scope_a, "source-a", "changed-a"), expected_revision=1)
        writer.put(MemoryWrite(scope_b, "source-b", "changed-b"), expected_revision=1)
        return 102

    store._clock_ms = write_during_clock
    result = review_coherent_snapshot(
        store, CoherentSnapshotRequest("fixture-owner", ("a", "b"))
    )
    assert seen == ["writer"]
    assert [group[0].content for group in result.records] == [
        "first record", "second record"
    ]
    assert writer.get(first.memory_id, scope_a).content == "changed-a"
    assert writer.get(second.memory_id, scope_b).content == "changed-b"


def test_reflected_request_change_during_clock_is_rejected(tmp_path):
    store, _, _, _, _ = _setup(tmp_path)
    req = CoherentSnapshotRequest("fixture-owner", ("a", "b"))

    def clock():
        object.__setattr__(req, "text", "different")
        return 102

    store._clock_ms = clock
    with pytest.raises(MemorySchemaError, match="changed during"):
        review_coherent_snapshot(store, req)


def test_query_and_limit_use_stable_deterministic_ranking(tmp_path):
    store, scope_a, _, _, _ = _setup(tmp_path)
    store.put(MemoryWrite(scope_a, "another", "first search match"))
    req = CoherentSnapshotRequest(
        "fixture-owner", ("a",), text="first", per_namespace_limit=1
    )
    result = review_coherent_snapshot(store, req)
    assert len(result.records[0]) == 1
    assert "first" in result.records[0][0].content
    assert (
        review_coherent_snapshot(store, req).provenance_sha256
        == result.provenance_sha256
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("per_namespace_limit", True),
        ("include_expired", 1),
        ("text", object()),
    ],
)
def test_strict_snapshot_carrier_types(field, value):
    kwargs = {field: value}
    with pytest.raises((TypeError, ValueError)):
        CoherentSnapshotRequest("fixture-owner", ("a",), **kwargs)
