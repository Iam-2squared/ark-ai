"""Run547: expiry preview cannot inherit replacement False-valued consent."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as mod


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "memory.sqlite3", clock_ms=lambda: 1_000,
    )
    scope = MemoryScope("owner-private", "notes")
    return store, scope


def _preview(store, scope):
    return mod.review_memory_expiry_candidates(
        store, scope, now_ms=1_500, limit=10,
    )


def test_unmodified_empty_expiry_preview_remains_non_authorizing(tmp_path):
    store, scope = _fixture(tmp_path)
    report = _preview(store, scope)
    assert report.candidate_count == 0
    assert report.deletion_authorized is False
    assert report.physical_erasure_proven is False
    assert mod.verify_memory_expiry_preview(
        report, store, scope, now_ms=1_500, limit=10,
        retained_preview_sha256=report.preview_sha256,
    ) is None


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_replaced_false_denial_property_rejected_at_preview(
    tmp_path, monkeypatch, flag,
):
    store, scope = _fixture(tmp_path)
    monkeypatch.setattr(
        mod.MemoryExpiryPreview, flag, property(lambda _self: False),
    )
    with pytest.raises(
        mod.MemoryExpiryPreviewRejected,
        match="authority descriptor changed",
    ):
        _preview(store, scope)


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_replaced_false_denial_property_rejected_at_reverification(
    tmp_path, monkeypatch, flag,
):
    store, scope = _fixture(tmp_path)
    previous = _preview(store, scope)
    monkeypatch.setattr(
        mod.MemoryExpiryPreview, flag, property(lambda _self: False),
    )
    with pytest.raises(
        mod.MemoryExpiryPreviewRejected,
        match="authority descriptor changed",
    ):
        mod.verify_memory_expiry_preview(
            previous, store, scope, now_ms=1_500, limit=10,
            retained_preview_sha256=previous.preview_sha256,
        )
