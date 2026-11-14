"""Memory expiry preview pins its digest protocol before private reads.

All data is disposable, read-only during review, and carries no consent,
trusted clock, external-disclosure authority or physical-erasure permission.
"""

from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as expiry


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "expiry-digest.sqlite3", clock_ms=lambda: 1_000,
    )
    scope = MemoryScope("fixture-owner", "private")
    store.put(MemoryWrite(scope, "note", "private fixture", expires_at_ms=1_200))
    report = expiry.review_memory_expiry_candidates(store, scope, now_ms=1_500)
    assert report.candidate_count == 1
    return store, scope, report


@pytest.mark.parametrize("phase", ("preview", "verify"))
@pytest.mark.parametrize("mutation", ("hashlib", "json", "sha256", "dumps", "domain"))
def test_digest_protocol_rebinding_refused_before_private_sqlite(
    tmp_path, monkeypatch, phase, mutation,
):
    store, scope, report = _fixture(tmp_path)
    called = []

    def forbidden(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("untrusted digest or private SQLite callback executed")

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden)
        if mutation == "hashlib":
            patch.setattr(expiry, "hashlib", SimpleNamespace(sha256=forbidden))
        elif mutation == "json":
            patch.setattr(expiry, "json", SimpleNamespace(dumps=forbidden))
        elif mutation == "sha256":
            patch.setattr(expiry.hashlib, "sha256", forbidden)
        elif mutation == "dumps":
            patch.setattr(expiry.json, "dumps", forbidden)
        else:
            patch.setattr(expiry, "_DOMAIN", b"counterfeit-expiry-preview-domain")
        with pytest.raises(
            expiry.MemoryExpiryPreviewRejected, match="expiry digest protocol changed",
        ):
            if phase == "preview":
                expiry.review_memory_expiry_candidates(
                    store, scope, now_ms=1_500,
                )
            else:
                expiry.verify_memory_expiry_preview(
                    report, store, scope, now_ms=1_500, limit=100,
                    retained_preview_sha256=report.preview_sha256,
                )

    assert called == []
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)


def test_restored_digest_protocol_still_verifies_without_erasure(tmp_path):
    store, scope, original = _fixture(tmp_path)
    report = expiry.review_memory_expiry_candidates(store, scope, now_ms=1_500)
    assert report.preview_sha256 == original.preview_sha256
    assert expiry.verify_memory_expiry_preview(
        report, store, scope, now_ms=1_500, limit=100,
        retained_preview_sha256=original.preview_sha256,
    ) is None
    assert report.deletion_authorized is False
    assert report.owner_consent_authenticated is False
    assert report.trusted_clock_verified is False
