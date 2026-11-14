"""Retained Memory comparison denies forged parser, codec and source slots.

Every fixture is local and synthetic. A digest comparison cannot certify
historical custody, ownership, deletion or authorization to disclose Memory.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.memory import retained_epoch_review as retained
from ark.memory.atomic_epoch_review import review_atomic_memory_epoch
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _pair(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-protocol.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("fixture-owner", "private")
    store.put(
        MemoryWrite(scope, "synthetic-source", "local secret only"),
        expected_revision=0,
    )
    return (
        review_atomic_memory_epoch(store, (scope,)),
        review_atomic_memory_epoch(store, (scope,)),
    )


@pytest.mark.parametrize(
    "name",
    ("_SHA", "_DOMAIN", "_MAX_ROWS", "_MAX_EVENTS", "_SQLITE_MAX"),
)
def test_rebound_parser_or_limits_fail_before_private_scope_read(
    tmp_path, monkeypatch, name,
):
    previous, current = _pair(tmp_path)
    changed = 10**20 if name.startswith("_MAX") or name == "_SQLITE_MAX" else object()
    with monkeypatch.context() as patch:
        patch.setattr(retained, name, changed)
        with pytest.raises(
            MemorySchemaError, match="retained Memory parser or codec changed",
        ):
            retained.review_retained_memory_epoch(previous, current)


@pytest.mark.parametrize("name", ("hashlib", "json"))
def test_codec_substitution_is_rejected_without_callback(
    tmp_path, monkeypatch, name,
):
    previous, current = _pair(tmp_path)
    called = []

    def hostile(*_a, **_kw):
        called.append("private digest leaked")
        raise AssertionError("forged codec must not receive private scope hashes")

    replacement = (
        SimpleNamespace(sha256=hostile) if name == "hashlib"
        else SimpleNamespace(dumps=hostile)
    )
    with monkeypatch.context() as patch:
        patch.setattr(retained, name, replacement)
        with pytest.raises(
            MemorySchemaError, match="retained Memory parser or codec changed",
        ):
            retained.review_retained_memory_epoch(previous, current)
    assert called == []


@pytest.mark.parametrize("name", ("scope_fingerprints", "content_digest"))
def test_retained_input_slot_injection_never_invokes_getter(
    tmp_path, monkeypatch, name,
):
    previous, current = _pair(tmp_path)
    called = []

    def hostile(_self):
        called.append(name)
        raise AssertionError("private review field was read by a fake getter")

    with monkeypatch.context() as patch:
        patch.setattr(retained._REVIEW_TYPE, name, property(hostile))
        with pytest.raises(
            MemorySchemaError, match="retained Memory review carrier changed",
        ):
            retained.review_retained_memory_epoch(previous, current)
    assert called == []


@pytest.mark.parametrize("name", ("status", "comparison_digest"))
def test_result_slot_replacement_never_invokes_getter(
    tmp_path, monkeypatch, name,
):
    previous, current = _pair(tmp_path)
    called = []

    def hostile(_self):
        called.append(name)
        raise AssertionError("forged result getter was invoked")

    with monkeypatch.context() as patch:
        patch.setattr(retained._COMPARISON_TYPE, name, property(hostile))
        with pytest.raises(
            MemorySchemaError, match="retained Memory comparison field changed",
        ):
            retained.review_retained_memory_epoch(previous, current)
    assert called == []


def test_unmodified_retained_comparison_is_denial_only(tmp_path):
    result = retained.review_retained_memory_epoch(*_pair(tmp_path))
    assert result.status == "UNCHANGED_LOCAL_CONTENT"
    assert result.new_event_counts == (0,)
    assert result.historical_prefix_proven is False
    assert result.independent_writer_proven is False
    assert result.custody_authenticated is False
    assert result.dispatch_authorized is False
    assert result.memory_disclosure_authorized is False
