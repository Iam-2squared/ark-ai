"""Memory expiry preview must not execute counterfeit class descriptors.

Read-only, disposable SQLite fixtures only; no purge, consent or disclosure.
"""

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as expiry


class CounterfeitDescriptor:
    def __init__(self, original, executed):
        self.original = original
        self.executed = executed

    def __get__(self, instance, owner=None):
        # If accidentally called on the CLASS, impersonate the original
        # property. Instance reads return the expected inert False.
        self.executed.append("descriptor")
        return self.original if instance is None else False


def _inputs(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "synthetic-expiry.sqlite3", clock_ms=lambda: 1_000,
    )
    scope = MemoryScope("fixture-owner", "private")
    return store, scope


@pytest.mark.parametrize("flag", expiry._FLAGS)
def test_class_level_counterfeit_is_never_invoked_before_preview(
    tmp_path, monkeypatch, flag,
):
    store, scope = _inputs(tmp_path)
    executed = []
    original = vars(expiry.MemoryExpiryPreview)[flag]
    monkeypatch.setattr(
        expiry.MemoryExpiryPreview, flag, CounterfeitDescriptor(original, executed),
    )
    with pytest.raises(
        expiry.MemoryExpiryPreviewRejected, match="authority descriptor changed",
    ):
        expiry.review_memory_expiry_candidates(store, scope, now_ms=1_500)
    assert executed == []


@pytest.mark.parametrize("flag", expiry._FLAGS)
def test_class_level_counterfeit_is_never_invoked_during_reverification(
    tmp_path, monkeypatch, flag,
):
    store, scope = _inputs(tmp_path)
    receipt = expiry.review_memory_expiry_candidates(
        store, scope, now_ms=1_500, limit=10,
    )
    executed = []
    original = vars(expiry.MemoryExpiryPreview)[flag]
    monkeypatch.setattr(
        expiry.MemoryExpiryPreview, flag, CounterfeitDescriptor(original, executed),
    )
    with pytest.raises(
        expiry.MemoryExpiryPreviewRejected, match="authority descriptor changed",
    ):
        expiry.verify_memory_expiry_preview(
            receipt, store, scope, now_ms=1_500, limit=10,
            retained_preview_sha256=receipt.preview_sha256,
        )
    assert executed == []


def test_original_empty_page_still_reverifies_without_erasure(tmp_path):
    store, scope = _inputs(tmp_path)
    report = expiry.review_memory_expiry_candidates(
        store, scope, now_ms=1_500, limit=10,
    )
    assert report.candidate_count == 0
    assert report.deletion_authorized is False
    assert expiry.verify_memory_expiry_preview(
        report, store, scope, now_ms=1_500, limit=10,
        retained_preview_sha256=report.preview_sha256,
    ) is None
