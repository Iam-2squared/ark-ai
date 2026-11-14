"""Malformed retained expiry evidence cannot trigger a private SQLite read.

Only synthetic receipts and local fixture data; no erasure/consent authority.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as preview


class PrivateStoreTrap:
    def __getattribute__(self, _name: str) -> object:
        raise AssertionError("private SQLite source accessed before receipt validation")


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("scope_sha256", "bad"),
        ("scope_sha256", object()),
        ("read_at_ms", True),
        ("read_at_ms", 101),
        ("candidate_count", True),
        ("candidate_count", -1),
        ("candidate_count", 11),
        ("has_more", 1),
        ("candidate_sha256", 7),
        ("preview_sha256", "d" * 64),
    ),
)
def test_invalid_retained_receipt_fails_before_private_store(
    field: str, value: object,
) -> None:
    original = preview.MemoryExpiryPreview(
        "a" * 64, 100, 0, False, "b" * 64, "c" * 64,
    )
    forged = replace(original, **{field: value})
    with pytest.raises(
        preview.MemoryExpiryPreviewRejected, match="retained expiry preview mismatch",
    ):
        preview.verify_memory_expiry_preview(
            forged, PrivateStoreTrap(), object(),
            now_ms=100, limit=10, retained_preview_sha256="c" * 64,
        )


@pytest.mark.parametrize(
    ("now_ms", "limit"),
    ((True, 10), (100, True), (-1, 10), (100, 0), (100, 1001)),
)
def test_invalid_verification_budget_fails_before_private_store(
    now_ms: object, limit: object,
) -> None:
    receipt = preview.MemoryExpiryPreview(
        "a" * 64, 100, 0, False, "b" * 64, "c" * 64,
    )
    with pytest.raises(
        preview.MemoryExpiryPreviewRejected, match="retained expiry preview mismatch",
    ):
        preview.verify_memory_expiry_preview(
            receipt, PrivateStoreTrap(), object(),
            now_ms=now_ms, limit=limit,
            retained_preview_sha256="c" * 64,
        )


def test_valid_retained_expiry_recheck_is_readonly(tmp_path) -> None:
    store = SQLiteMemoryStore(
        tmp_path / "expiring-fixture.sqlite", clock_ms=lambda: 200,
    )
    scope = MemoryScope("synthetic", "private")
    item = store.put(
        MemoryWrite(scope, "fixture", "nonprivate test text", expires_at_ms=300),
    )
    receipt = preview.review_memory_expiry_candidates(
        store, scope, now_ms=400, limit=10,
    )
    assert receipt.candidate_count == 1
    assert preview.verify_memory_expiry_preview(
        receipt, store, scope, now_ms=400, limit=10,
        retained_preview_sha256=receipt.preview_sha256,
    ) is None
    assert store.get(item.memory_id, scope) is not None
    assert receipt.deletion_authorized is False
