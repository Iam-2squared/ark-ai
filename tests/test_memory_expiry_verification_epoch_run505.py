"""Bounded expiry receipts must resist spoofed equality and denial callbacks."""

from dataclasses import replace

import pytest

import ark.memory.expiry_candidate_preview as mod
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "expiry-check.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("private-owner", "scratch")
    first = store.put(
        MemoryWrite(scope, "one", "private", expires_at_ms=1200),
    )
    store.put(MemoryWrite(scope, "two", "more private", expires_at_ms=1500))
    return store, scope, first


def preview(store, scope):
    return mod.review_memory_expiry_candidates(
        store, scope, now_ms=1500, limit=10,
    )


def verify(receipt, store, scope, retained):
    return mod.verify_memory_expiry_preview(
        receipt, store, scope, now_ms=1500, limit=10,
        retained_preview_sha256=retained,
    )


@pytest.mark.parametrize("field,value", [
    ("candidate_count", 99),
    ("candidate_sha256", "f" * 64),
    ("scope_sha256", "f" * 64),
    ("read_at_ms", 1499),
    ("has_more", True),
])
def test_forged_equal_receipt_rejected(tmp_path, monkeypatch, field, value):
    store, scope, _ = fixture(tmp_path)
    original = preview(store, scope)
    forged = replace(original, **{field: value})
    monkeypatch.setattr(
        mod.MemoryExpiryPreview, "__eq__", lambda self, other: True,
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="mismatch"):
        verify(forged, store, scope, original.preview_sha256)


@pytest.mark.parametrize("mutation", ["receipt", "scope", "page"])
def test_final_denial_getter_cannot_conceal_mutation(
    tmp_path, monkeypatch, mutation,
):
    store, scope, first = fixture(tmp_path)
    original = preview(store, scope)

    def late_denial(self):
        if self is original:
            if mutation == "receipt":
                object.__setattr__(self, "candidate_sha256", "f" * 64)
            elif mutation == "scope":
                object.__setattr__(scope, "namespace", "other")
            else:
                store.put(
                    MemoryWrite(scope, "one", "future", expires_at_ms=2600),
                    expected_revision=first.revision,
                )
        return False

    monkeypatch.setattr(
        mod.MemoryExpiryPreview, "external_disclosure_authorized",
        property(late_denial),
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="changed"):
        verify(original, store, scope, original.preview_sha256)


def test_local_creation_checks_denial_side_effects(tmp_path, monkeypatch):
    store, scope, _ = fixture(tmp_path)

    def mutate(self):
        object.__setattr__(self, "candidate_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        mod.MemoryExpiryPreview, "external_disclosure_authorized",
        property(mutate),
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="changed"):
        preview(store, scope)


def test_unmodified_receipt_remains_read_only(tmp_path):
    store, scope, _ = fixture(tmp_path)
    before = tuple(store.events(scope))
    receipt = preview(store, scope)
    assert verify(receipt, store, scope, receipt.preview_sha256) is None
    assert tuple(store.events(scope)) == before
    assert receipt.deletion_authorized is False
