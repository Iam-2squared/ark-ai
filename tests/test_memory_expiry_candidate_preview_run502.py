"""Read-only expiry candidate snapshots; never call purge_expired."""

from dataclasses import replace

import pytest

import ark.memory.expiry_candidate_preview as mod
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "memory.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("owner-private", "notes")
    other = MemoryScope("other-owner", "notes")
    first = store.put(MemoryWrite(scope, "a", "secret-1", expires_at_ms=1200))
    store.put(MemoryWrite(scope, "b", "secret-2", expires_at_ms=1500))
    store.put(MemoryWrite(scope, "c", "secret-3", expires_at_ms=1500))
    store.put(MemoryWrite(scope, "d", "future", expires_at_ms=2500))
    store.put(MemoryWrite(scope, "e", "never"))
    store.put(MemoryWrite(other, "a", "foreign", expires_at_ms=1200))
    return store, scope, first


def preview(store, scope, now_ms=1500, limit=100):
    return mod.review_memory_expiry_candidates(
        store, scope, now_ms=now_ms, limit=limit,
    )


def test_same_snapshot_and_boundaries(tmp_path):
    store, scope, _ = fixture(tmp_path)
    result = preview(store, scope)
    assert result == preview(store, scope)
    assert result.candidate_count == 3
    assert result.has_more is False
    assert len(result.preview_sha256) == 64
    assert "secret" not in repr(result)
    assert "owner-private" not in repr(result)
    assert mod.verify_memory_expiry_preview(
        result, store, scope, now_ms=1500, limit=100,
        retained_preview_sha256=result.preview_sha256,
    ) is None
    for flag in mod._FLAGS:
        assert getattr(result, flag) is False


@pytest.mark.parametrize("now_ms,count", [
    (0, 0), (1199, 0), (1200, 1), (1499, 1), (1500, 3), (2500, 4),
])
def test_exact_expiry_clock_edge(now_ms, count, tmp_path):
    store, scope, _ = fixture(tmp_path)
    assert preview(store, scope, now_ms).candidate_count == count


def test_paging_does_not_claim_full_coverage(tmp_path):
    store, scope, _ = fixture(tmp_path)
    limited = preview(store, scope, limit=2)
    assert limited.candidate_count == 2
    assert limited.has_more is True
    assert limited.preview_sha256 != preview(store, scope, limit=3).preview_sha256
    assert limited.preview_sha256 != preview(store, scope, limit=100).preview_sha256


def test_store_not_mutated_by_preview(tmp_path):
    store, scope, first = fixture(tmp_path)
    original = store.get(first.memory_id, scope, include_expired=True)
    events = tuple(store.events(scope))
    preview(store, scope)
    assert store.get(first.memory_id, scope, include_expired=True) == original
    assert tuple(store.events(scope)) == events


def test_scope_isolation(tmp_path):
    store, scope, _ = fixture(tmp_path)
    other = MemoryScope("another-owner", "notes")
    report = preview(store, scope)
    assert preview(store, other).candidate_count == 0
    assert preview(store, other).scope_sha256 != report.scope_sha256


def test_stale_retained_snapshot_rejected_after_cas_update(tmp_path):
    store, scope, first = fixture(tmp_path)
    old = preview(store, scope)
    store.put(
        MemoryWrite(scope, "a", "retained", expires_at_ms=2600),
        expected_revision=first.revision,
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="mismatch"):
        mod.verify_memory_expiry_preview(
            old, store, scope, now_ms=1500, limit=100,
            retained_preview_sha256=old.preview_sha256,
        )


@pytest.mark.parametrize("bad_time,bad_limit", [
    (True, 100), (-1, 100), (2**63, 100), (0.1, 100),
    (1500, True), (1500, 0), (1500, 1001),
])
def test_invalid_untrusted_time_and_limit_denied(tmp_path, bad_time, bad_limit):
    store, scope, _ = fixture(tmp_path)
    with pytest.raises(mod.MemoryExpiryPreviewRejected):
        mod.review_memory_expiry_candidates(
            store, scope, now_ms=bad_time, limit=bad_limit,
        )


@pytest.mark.parametrize("field,value", [
    ("scope_sha256", "f" * 64),
    ("read_at_ms", True),
    ("candidate_count", True),
    ("candidate_count", 99),
    ("has_more", True),
    ("has_more", 1),
    ("candidate_sha256", "f" * 64),
    ("preview_sha256", "f" * 64),
])
def test_forged_preview_denied(tmp_path, field, value):
    store, scope, _ = fixture(tmp_path)
    previous = preview(store, scope)
    forged = replace(previous, **{field: value})
    with pytest.raises(mod.MemoryExpiryPreviewRejected):
        mod.verify_memory_expiry_preview(
            forged, store, scope, now_ms=1500, limit=100,
            retained_preview_sha256=previous.preview_sha256,
        )


def test_scope_changed_during_hydration_denied(tmp_path, monkeypatch):
    store, scope, _ = fixture(tmp_path)
    original = mod._record

    def mutate(row):
        object.__setattr__(scope, "namespace", "replaced")
        return original(row)

    monkeypatch.setattr(mod, "_record", mutate)
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="inputs changed"):
        preview(store, scope)


def test_retained_root_wrong_or_not_exact_text(tmp_path):
    store, scope, _ = fixture(tmp_path)
    original = preview(store, scope)
    for bad in (True, "f" * 64, "X" * 64, "bad"):
        with pytest.raises(mod.MemoryExpiryPreviewRejected):
            mod.verify_memory_expiry_preview(
                original, store, scope, now_ms=1500, limit=100,
                retained_preview_sha256=bad,
            )


@pytest.mark.parametrize("flag", mod._FLAGS)
def test_receipt_must_not_claim_deletion_or_consent(tmp_path, monkeypatch, flag):
    store, scope, _ = fixture(tmp_path)
    monkeypatch.setattr(
        mod.MemoryExpiryPreview, flag, property(lambda self: True),
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="authority"):
        preview(store, scope)


class ForgedExpiryPreview(mod.MemoryExpiryPreview):
    pass


def test_subclass_receipt_rejected(tmp_path):
    store, scope, _ = fixture(tmp_path)
    previous = preview(store, scope)
    forged = ForgedExpiryPreview(
        previous.scope_sha256, previous.read_at_ms,
        previous.candidate_count, previous.has_more,
        previous.candidate_sha256, previous.preview_sha256,
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="exact"):
        mod.verify_memory_expiry_preview(
            forged, store, scope, now_ms=1500, limit=100,
            retained_preview_sha256=previous.preview_sha256,
        )
