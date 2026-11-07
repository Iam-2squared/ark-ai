"""Expiry preview recheck pins receipt epoch and denies late authority drift.

All fixtures use local SQLite and synthetic timestamps; no physical deletion,
trusted clock, consent inference or external request is authorized.
"""

from __future__ import annotations

import pytest

import ark.memory.expiry_candidate_preview as preview
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "private-expiry.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("fixture-owner", "private")
    store.put(MemoryWrite(
        scope, "source", "fake-secret", {"tag": "test"}, expires_at_ms=900,
    ))
    receipt = preview.review_memory_expiry_candidates(
        store, scope, now_ms=1000, limit=10,
    )
    return store, scope, receipt


def _check(state):
    store, scope, receipt = state
    return preview.verify_memory_expiry_preview(
        receipt, store, scope, now_ms=1000, limit=10,
        retained_preview_sha256=receipt.preview_sha256,
    )


@pytest.mark.parametrize("field", (
    "scope_sha256", "candidate_sha256", "preview_sha256", "read_at_ms",
))
def test_equal_value_receipt_carrier_replacement_after_local_scan_rejected(
    tmp_path, monkeypatch, field,
):
    state = _case(tmp_path)
    receipt = state[2]
    original = preview.review_memory_expiry_candidates
    count = 0

    def reflected(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 2:
            prior = getattr(receipt, field)
            replacement = (
                int(str(prior))
                if field == "read_at_ms"
                else ("!" + prior)[1:]
            )
            assert replacement == prior and replacement is not prior
            object.__setattr__(receipt, field, replacement)
        return result

    monkeypatch.setattr(preview, "review_memory_expiry_candidates", reflected)
    with pytest.raises(preview.MemoryExpiryPreviewRejected, match="changed"):
        _check(state)
    assert count == 2


@pytest.mark.parametrize("flag", (
    "deletion_authorized", "external_disclosure_authorized",
))
def test_retained_receipt_cannot_gain_authority_at_final_scan(
    tmp_path, monkeypatch, flag,
):
    state = _case(tmp_path)
    receipt = state[2]
    original = preview.review_memory_expiry_candidates
    scans = 0
    armed = False

    def late_scan(*args, **kwargs):
        nonlocal scans, armed
        result = original(*args, **kwargs)
        scans += 1
        if scans == 2:
            armed = True
        return result

    monkeypatch.setattr(preview, "review_memory_expiry_candidates", late_scan)
    monkeypatch.setattr(
        preview.MemoryExpiryPreview, flag,
        property(lambda self: bool(armed and self is receipt)),
    )
    # Replacing a denial descriptor is now refused before either page scan.
    with pytest.raises(
        preview.MemoryExpiryPreviewRejected,
        match="authority descriptor changed",
    ):
        _check(state)
    assert scans == 0


@pytest.mark.parametrize("flag", (
    "deletion_authorized", "trusted_clock_verified",
))
def test_latest_page_receipt_cannot_gain_new_authority(
    tmp_path, monkeypatch, flag,
):
    state = _case(tmp_path)
    original = preview.review_memory_expiry_candidates
    latest = None
    scans = 0

    def late_scan(*args, **kwargs):
        nonlocal scans, latest
        result = original(*args, **kwargs)
        scans += 1
        if scans == 2:
            latest = result
        return result

    monkeypatch.setattr(preview, "review_memory_expiry_candidates", late_scan)
    monkeypatch.setattr(
        preview.MemoryExpiryPreview, flag,
        property(lambda self: bool(self is latest)),
    )
    # Replacing a denial descriptor is now refused before either page scan.
    with pytest.raises(
        preview.MemoryExpiryPreviewRejected,
        match="authority descriptor changed",
    ):
        _check(state)
    assert scans == 0


def test_retained_receipt_denial_getter_cannot_replace_equal_carrier(
    tmp_path, monkeypatch,
):
    state = _case(tmp_path)
    receipt = state[2]
    calls = 0

    def late_false(self):
        nonlocal calls
        if self is receipt:
            calls += 1
            if calls == 2:
                prior = self.scope_sha256
                replacement = ("!" + prior)[1:]
                assert replacement == prior and replacement is not prior
                object.__setattr__(self, "scope_sha256", replacement)
        return False

    monkeypatch.setattr(
        preview.MemoryExpiryPreview, "deletion_authorized", property(late_false),
    )
    # Even a False-valued replacement is now rejected before a getter runs.
    with pytest.raises(
        preview.MemoryExpiryPreviewRejected,
        match="authority descriptor changed",
    ):
        _check(state)
    assert calls == 0


def test_valid_review_is_read_only_and_non_authorizing(tmp_path):
    state = _case(tmp_path)
    store, scope, receipt = state
    original_events = tuple(store.events(scope))
    assert _check(state) is None
    assert tuple(store.events(scope)) == original_events
    assert receipt.deletion_authorized is False
    assert receipt.physical_erasure_proven is False
    assert receipt.trusted_clock_verified is False
