"""Memory expiry preview must reject replaced denial code before SQLite work.

All data are local dummy fixtures. Neither receipt grants erasure, ownership,
consent, trusted clock, or an automatic purge. No paid/backend action.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as mod


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "expiry-custody.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "notes")
    return store, scope


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_false_only_substitution_refused_before_sqlite(
    tmp_path, monkeypatch, flag,
):
    store, scope = _case(tmp_path)
    opened = []

    def forbidden_open(_store):
        opened.append(True)
        raise AssertionError("preview must reject before opening SQLite")

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_open)
    monkeypatch.setattr(
        mod.MemoryExpiryPreview, flag, property(lambda _self: False),
    )
    with pytest.raises(
        mod.MemoryExpiryPreviewRejected, match="authority descriptor changed",
    ):
        mod.review_memory_expiry_candidates(store, scope, now_ms=1001)
    assert opened == []


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_retained_expiry_reverification_refuses_substitution_before_sqlite(
    tmp_path, monkeypatch, flag,
):
    store, scope = _case(tmp_path)
    report = mod.review_memory_expiry_candidates(
        store, scope, now_ms=1001,
    )
    opened = []

    def forbidden_open(_store):
        opened.append(True)
        raise AssertionError("reverification must reject before opening SQLite")

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_open)
    monkeypatch.setattr(
        mod.MemoryExpiryPreview, flag, property(lambda _self: False),
    )
    with pytest.raises(
        mod.MemoryExpiryPreviewRejected, match="authority descriptor changed",
    ):
        mod.verify_memory_expiry_preview(
            report, store, scope, now_ms=1001, limit=100,
            retained_preview_sha256=report.preview_sha256,
        )
    assert opened == []


def test_denial_substitution_while_opening_sqlite_rejected(tmp_path, monkeypatch):
    store, scope = _case(tmp_path)
    original = SQLiteMemoryStore._connect_readonly
    opened = []

    def drift_during_open(instance):
        conn = original(instance)
        opened.append(True)
        monkeypatch.setattr(
            mod.MemoryExpiryPreview, "deletion_authorized",
            property(lambda _self: False),
        )
        return conn

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", drift_during_open)
    with pytest.raises(
        mod.MemoryExpiryPreviewRejected, match="authority descriptor changed",
    ):
        mod.review_memory_expiry_candidates(store, scope, now_ms=1001)
    assert opened == [True]
