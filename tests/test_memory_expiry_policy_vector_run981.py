"""Expiry preview refuses incomplete policy vectors before SQLite access.

Disposable local SQLite fixtures only. No purge, physical erasure, consent,
trusted-clock claim, external disclosure or automatic expiry mutation.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as expiry


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "expiry-policy-vector.sqlite3", clock_ms=lambda: 1_000,
    )
    scope = MemoryScope("owner", "notes")
    store.put(MemoryWrite(scope, "source", "private", expires_at_ms=1_200))
    receipt = expiry.review_memory_expiry_candidates(store, scope, now_ms=1_500)
    assert receipt.candidate_count == 1
    return store, scope, receipt


@pytest.mark.parametrize("phase", ("preview", "verify"))
@pytest.mark.parametrize("vector", (
    "_FLAGS", "_RECEIPT_FIELDS", "_RECEIPT_HOOKS",
))
@pytest.mark.parametrize("mutation", ("empty", "reordered", "equal_rebound"))
def test_expiry_policy_vector_rebind_refused_before_private_read(
    tmp_path, monkeypatch, phase, vector, mutation,
):
    store, scope, receipt = _fixture(tmp_path)
    called = []

    def forbidden(self):
        called.append(True)
        raise AssertionError("unverified expiry private SQLite reader executed")

    original = getattr(expiry, vector)
    assert len(original) > 1
    if mutation == "empty":
        changed = ()
    elif mutation == "reordered":
        changed = tuple(reversed(original))
    else:
        changed = tuple(list(original))
        assert changed == original and changed is not original

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden)
        patch.setattr(expiry, vector, changed)
        with pytest.raises(
            expiry.MemoryExpiryPreviewRejected, match="policy vector changed",
        ):
            if phase == "preview":
                expiry.review_memory_expiry_candidates(store, scope, now_ms=1_500)
            else:
                expiry.verify_memory_expiry_preview(
                    receipt, store, scope, now_ms=1_500, limit=100,
                    retained_preview_sha256=receipt.preview_sha256,
                )
    assert called == []


def test_shrunk_denial_list_cannot_hide_forged_deletion_getter(
    tmp_path, monkeypatch,
):
    store, scope, _ = _fixture(tmp_path)
    called = []

    def forged(self):
        called.append(True)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(expiry, "_FLAGS", ())
        patch.setattr(
            expiry.MemoryExpiryPreview, "deletion_authorized", property(forged),
        )
        with pytest.raises(
            expiry.MemoryExpiryPreviewRejected, match="policy vector changed",
        ):
            expiry.review_memory_expiry_candidates(store, scope, now_ms=1_500)
    assert called == []


def test_original_expiry_preview_remains_read_only(tmp_path):
    store, scope, receipt = _fixture(tmp_path)
    assert receipt.deletion_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.owner_consent_authenticated is False
    assert receipt.physical_erasure_proven is False
    assert expiry.verify_memory_expiry_preview(
        receipt, store, scope, now_ms=1_500, limit=100,
        retained_preview_sha256=receipt.preview_sha256,
    ) is None
