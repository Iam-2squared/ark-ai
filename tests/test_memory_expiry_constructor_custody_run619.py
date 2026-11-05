"""Offline Memory expiry preview rejects swapped constructors before execution.

All Memory rows are disposable. No physical purge, consent or backend exists.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as expiry


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "synthetic-expiry.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("fixture-owner", "private")
    store.put(MemoryWrite(scope, "note", "fixture", expires_at_ms=1200))
    return store, scope


@pytest.mark.parametrize("phase", ("preview", "verify"))
def test_preinstalled_constructor_drift_refused_before_database_read(
    tmp_path, monkeypatch, phase,
):
    store, scope = _case(tmp_path)
    report = expiry.review_memory_expiry_candidates(store, scope, now_ms=1500)
    called = []

    def counterfeit_init(self, *args):
        called.append("constructor")

    def unexpected_read(self):
        called.append("sqlite")
        raise AssertionError("must reject before reading Memory")

    monkeypatch.setattr(expiry.MemoryExpiryPreview, "__init__", counterfeit_init)
    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", unexpected_read)
    with pytest.raises(expiry.MemoryExpiryPreviewRejected, match="authority"):
        if phase == "preview":
            expiry.review_memory_expiry_candidates(store, scope, now_ms=1500)
        else:
            expiry.verify_memory_expiry_preview(
                report, store, scope, now_ms=1500, limit=100,
                retained_preview_sha256=report.preview_sha256,
            )
    assert called == []


@pytest.mark.parametrize("boundary", ("row", "final_digest"))
def test_constructor_rebinding_during_preview_never_invokes_counterfeit(
    tmp_path, monkeypatch, boundary,
):
    store, scope = _case(tmp_path)
    original_row = expiry._record
    original_hash = expiry._hash
    called = []
    replaced = []

    def inject():
        if replaced:
            return
        replaced.append(True)

        def counterfeit_init(self, *args):
            called.append("constructor")

        monkeypatch.setattr(expiry.MemoryExpiryPreview, "__init__",
                            counterfeit_init)

    def row_hook(row):
        result = original_row(row)
        if boundary == "row":
            inject()
        return result

    def hash_hook(tag, value):
        result = original_hash(tag, value)
        if tag == "preview" and boundary == "final_digest":
            inject()
        return result

    monkeypatch.setattr(expiry, "_record", row_hook)
    monkeypatch.setattr(expiry, "_hash", hash_hook)
    with pytest.raises(expiry.MemoryExpiryPreviewRejected, match="authority"):
        expiry.review_memory_expiry_candidates(store, scope, now_ms=1500)
    assert replaced == [True]
    assert called == []


def test_unchanged_expiry_receipt_still_verifies_without_erasure(tmp_path):
    store, scope = _case(tmp_path)
    before = tuple(store.events(scope))
    report = expiry.review_memory_expiry_candidates(store, scope, now_ms=1500)
    assert report.candidate_count == 1
    assert report.deletion_authorized is False
    assert expiry.verify_memory_expiry_preview(
        report, store, scope, now_ms=1500, limit=100,
        retained_preview_sha256=report.preview_sha256,
    ) is None
    assert tuple(store.events(scope)) == before
