"""Run1385: coherent snapshot validator vectors retain their import-time identity."""

from __future__ import annotations

import pytest

import ark.memory.coherent_snapshot_review as snapshot
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "snapshot.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(MemoryScope("synthetic-owner", "notes"), "source", "local-only"))
    request = snapshot.CoherentSnapshotRequest("synthetic-owner", ("notes",))
    return store, request


def test_request_validator_rejects_joint_vector_rebinding_before_field_access(
    tmp_path, monkeypatch,
):
    store, request = _fixture(tmp_path)
    getter_calls = []

    def hostile_getter(_instance):
        getter_calls.append(True)
        raise AssertionError("replaced request field descriptor executed")

    # A class-level slot replacement is executable when the request is read.
    monkeypatch.setattr(
        snapshot.CoherentSnapshotRequest, "owner_id", property(hostile_getter),
    )
    for name in (
        "_REQUEST_FIELDS",
        "_ORIGINAL_REQUEST_FIELDS",
        "_REQUEST_HOOKS",
        "_ORIGINAL_REQUEST_HOOKS",
    ):
        monkeypatch.setattr(snapshot, name, ())

    with pytest.raises(MemorySchemaError, match="request validator changed"):
        snapshot.review_coherent_snapshot(store, request)

    assert getter_calls == []


def test_result_constructor_rejects_joint_vector_rebinding_before_new(
    tmp_path, monkeypatch,
):
    store, request = _fixture(tmp_path)
    constructor_calls = []
    result_type = snapshot.CoherentSnapshotReview
    had_own_new = "__new__" in vars(result_type)
    original_new = vars(result_type).get("__new__")

    def hostile_new(cls, *_args, **_kwargs):
        constructor_calls.append(True)
        raise AssertionError("replaced snapshot result __new__ executed")

    result_type.__new__ = staticmethod(hostile_new)
    try:
        for name in (
            "_RESULT_FIELDS",
            "_ORIGINAL_RESULT_FIELDS",
            "_RESULT_HOOKS",
            "_ORIGINAL_RESULT_HOOKS",
        ):
            monkeypatch.setattr(snapshot, name, ())

        with pytest.raises(MemorySchemaError, match="result constructor changed"):
            snapshot.review_coherent_snapshot(store, request)
    finally:
        if had_own_new:
            result_type.__new__ = original_new
        else:
            delattr(result_type, "__new__")

    assert constructor_calls == []
