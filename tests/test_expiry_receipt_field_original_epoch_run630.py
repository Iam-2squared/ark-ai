"""Run630: expiry previews reject executable receipt hooks before any call."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import expiry_candidate_preview as mod


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "expiry-custody.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("private-owner", "notes")
    store.put(MemoryWrite(scope, "note", "secret", expires_at_ms=1200))
    return store, scope


@pytest.mark.parametrize("field", [
    "__init__", "__getattr__", "__getattribute__",
    "candidate_count", "preview_sha256", "deletion_authorized",
])
def test_preview_refuses_preinstalled_executable_carriers(
    tmp_path, monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    store, scope = _fixture(tmp_path)
    original_events = tuple(store.events(scope))
    invoked: list[str] = []

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append(field)
        raise AssertionError("substituted expiry receipt hook executed")

    monkeypatch.setattr(mod.MemoryExpiryPreview, field, poisoned, raising=False)
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="authority"):
        mod.review_memory_expiry_candidates(store, scope, now_ms=1300)
    assert invoked == []
    assert tuple(store.events(scope)) == original_events


def test_existing_receipt_verification_refuses_replaced_field_getter(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope = _fixture(tmp_path)
    receipt = mod.review_memory_expiry_candidates(store, scope, now_ms=1300)
    retained_digest = receipt.preview_sha256
    invoked: list[str] = []

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append("getattribute")
        raise AssertionError("retained receipt getter executed")

    monkeypatch.setattr(
        mod.MemoryExpiryPreview, "__getattribute__", poisoned,
    )
    with pytest.raises(mod.MemoryExpiryPreviewRejected, match="authority"):
        mod.verify_memory_expiry_preview(
            receipt, store, scope, now_ms=1300, limit=100,
            retained_preview_sha256=retained_digest,
        )
    assert invoked == []


def test_digest_time_constructor_replacement_is_refused(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scope = _fixture(tmp_path)
    invoked: list[str] = []
    original_digest = mod.hashlib.sha256
    original_init = mod.MemoryExpiryPreview.__init__

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append("init")
        raise AssertionError("substituted receipt initializer executed")

    def digest(raw: bytes = b""):
        if raw.startswith(mod._DOMAIN + b"preview" + bytes((0,))):
            monkeypatch.setattr(mod.MemoryExpiryPreview, "__init__", poisoned)
        return original_digest(raw)

    monkeypatch.setattr(mod.hashlib, "sha256", digest)
    try:
        # A pinned digest authority may reject before invoking the injected digest.
        # Earlier fail-closed rejection and the constructor guard are both valid.
        with pytest.raises(
            mod.MemoryExpiryPreviewRejected,
            match="authority|expiry digest protocol changed",
        ):
            mod.review_memory_expiry_candidates(store, scope, now_ms=1300)
        assert invoked == []
    finally:
        monkeypatch.setattr(mod.MemoryExpiryPreview, "__init__", original_init)


def test_normal_expiry_preview_stays_read_only(tmp_path) -> None:
    store, scope = _fixture(tmp_path)
    events = tuple(store.events(scope))
    result = mod.review_memory_expiry_candidates(store, scope, now_ms=1300)
    assert result.candidate_count == 1
    assert result.deletion_authorized is False
    assert result.owner_consent_authenticated is False
    assert mod.verify_memory_expiry_preview(
        result, store, scope, now_ms=1300, limit=100,
        retained_preview_sha256=result.preview_sha256,
    ) is None
    assert tuple(store.events(scope)) == events
