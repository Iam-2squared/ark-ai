"""Context preview denial-only getters must not mutate returned private fixtures."""

import hashlib

import pytest

from ark import personal_context_offline_preview as mod


def _fixture():
    content = "synthetic private context"
    return mod.OfflineContextFixture(
        "rec_" + "1" * 32, "a" * 64, "b" * 64, content,
        hashlib.sha256(content.encode()).hexdigest(), 2000,
    )


def _preview(row):
    return mod.build_offline_context_preview(
        (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
    )


def test_stable_preview_preserves_canonical_private_fixture():
    result = _preview(_fixture())
    assert "synthetic private context" in result.canonical_local_json
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.retention_authorized is False


def test_last_authority_getter_cannot_mutate_returned_preview(monkeypatch):
    def late_swap(self):
        object.__setattr__(self, "canonical_local_json", "{}")
        return False

    monkeypatch.setattr(
        mod.OfflineContextPreview, "retention_authorized", property(late_swap),
    )
    with pytest.raises(mod.OfflineContextPreviewRejected, match="after authority"):
        _preview(_fixture())


def test_last_authority_getter_cannot_mutate_original_record(monkeypatch):
    row = _fixture()

    def late_swap(_self):
        object.__setattr__(row, "content", "replaced after digest")
        return False

    monkeypatch.setattr(
        mod.OfflineContextPreview, "retention_authorized", property(late_swap),
    )
    with pytest.raises(mod.OfflineContextPreviewRejected, match="fixture changed"):
        _preview(row)


def test_last_authority_getter_cannot_mutate_record_ids(monkeypatch):
    def late_swap(self):
        object.__setattr__(self, "record_ids", ("rec_" + "f" * 32,))
        return False

    monkeypatch.setattr(
        mod.OfflineContextPreview, "retention_authorized", property(late_swap),
    )
    with pytest.raises(mod.OfflineContextPreviewRejected, match="after authority"):
        _preview(_fixture())
