"""Static request/result descriptor custody for local coherent Memory reads.

Synthetic SQLite only: no personal-data connector, deletion, external write or
consent assumption. A hostile getter is never invoked on the rejection path.
"""

from __future__ import annotations

import pytest

from ark.memory import coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _case(tmp_path, *, clock=None):
    store = SQLiteMemoryStore(
        tmp_path / "coherent-slots.sqlite",
        clock_ms=clock if clock is not None else lambda: 100,
    )
    scope = MemoryScope("synthetic-owner", "private")
    saved = store.put(MemoryWrite(scope, "source", "fixture-only text"))
    request = snapshot.CoherentSnapshotRequest(scope.owner_id, (scope.namespace,))
    return store, request, saved


@pytest.mark.parametrize("target", ("request", "result"))
@pytest.mark.parametrize("member", ("__getattribute__", "__getattr__"))
def test_preinstalled_lookup_hook_refused_before_execution(
    tmp_path, monkeypatch, target, member,
):
    store, request, saved = _case(tmp_path)
    invoked: list[str] = []

    def hostile(*_args, **_kwargs):
        invoked.append(member)
        raise AssertionError("hostile descriptor invoked")

    carrier = (
        snapshot.CoherentSnapshotRequest if target == "request"
        else snapshot.CoherentSnapshotReview
    )
    monkeypatch.setattr(carrier, member, hostile, raising=False)
    with pytest.raises(
        MemorySchemaError,
        match="request validator changed" if target == "request"
        else "result constructor changed",
    ):
        snapshot.review_coherent_snapshot(store, request)
    assert invoked == []
    assert store.get(saved.memory_id, saved.scope).content == "fixture-only text"


@pytest.mark.parametrize(
    "member",
    ("owner_id", "namespaces", "text", "per_namespace_limit", "include_expired"),
)
def test_preinstalled_request_slot_refused_before_read(
    tmp_path, monkeypatch, member,
):
    store, request, _ = _case(tmp_path)
    invoked: list[str] = []

    def hostile(_self):
        invoked.append(member)
        raise AssertionError("request getter ran")

    monkeypatch.setattr(
        snapshot.CoherentSnapshotRequest, member, property(hostile),
    )
    with pytest.raises(MemorySchemaError, match="request validator changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert invoked == []


@pytest.mark.parametrize(
    "member", ("read_at_ms", "scopes", "records", "provenance_sha256"),
)
def test_preinstalled_result_slot_refused_before_read(
    tmp_path, monkeypatch, member,
):
    store, request, _ = _case(tmp_path)
    invoked: list[str] = []

    def hostile(_self):
        invoked.append(member)
        raise AssertionError("result getter ran")

    monkeypatch.setattr(snapshot.CoherentSnapshotReview, member, property(hostile))
    with pytest.raises(MemorySchemaError, match="result constructor changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert invoked == []


def test_clock_callback_rebinding_request_slot_is_rejected_before_lookup(
    tmp_path, monkeypatch,
):
    armed = [False]
    invoked: list[str] = []

    def hostile(_self):
        invoked.append("text")
        raise AssertionError("clock-injected request getter ran")

    def clock():
        if armed[0]:
            monkeypatch.setattr(
                snapshot.CoherentSnapshotRequest, "text", property(hostile),
            )
        return 100

    store, request, _ = _case(tmp_path, clock=clock)
    armed[0] = True
    with pytest.raises(MemorySchemaError, match="request validator changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert invoked == []


def test_digest_callback_rebinding_result_slot_is_rejected_before_lookup(
    tmp_path, monkeypatch,
):
    store, request, _ = _case(tmp_path)
    invoked: list[str] = []
    triggered: list[str] = []
    original = snapshot.hashlib.sha256

    def hostile(_self):
        invoked.append("records")
        raise AssertionError("digest-injected result getter ran")

    def injected_digest(payload=b""):
        if b'"witness_format_version":2' in payload:
            triggered.append("digest")
            monkeypatch.setattr(
                snapshot.CoherentSnapshotReview, "records", property(hostile),
            )
        return original(payload)

    monkeypatch.setattr(snapshot.hashlib, "sha256", injected_digest)
    with pytest.raises(MemorySchemaError, match="result constructor changed"):
        snapshot.review_coherent_snapshot(store, request)
    assert triggered == ["digest"]
    assert invoked == []


def test_unmodified_coherent_snapshot_still_has_content_free_witness(tmp_path):
    store, request, saved = _case(tmp_path)
    report = snapshot.review_coherent_snapshot(store, request)
    assert report.records[0][0].memory_id == saved.memory_id
    assert report.scopes == (saved.scope,)
    assert len(report.provenance_sha256) == 64
