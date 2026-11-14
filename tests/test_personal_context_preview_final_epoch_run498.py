"""Context preview forbids changed lookup machinery before private reads."""

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
    original = mod.OfflineContextPreview.__getattribute__

    def late_swap(self, name):
        result = original(self, name)
        if name == "retention_authorized":
            object.__setattr__(self, "canonical_local_json", "{}")
        return result

    # A substituted lookup hook is refused before it executes.
    # Later mutation expectations must not bypass the original guard.
    monkeypatch.setattr(mod.OfflineContextPreview, "__getattribute__", late_swap)
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _preview(_fixture())


def test_last_authority_getter_cannot_mutate_original_record(monkeypatch):
    row = _fixture()

    original = mod.OfflineContextPreview.__getattribute__

    def late_swap(self, name):
        result = original(self, name)
        if name == "retention_authorized":
            object.__setattr__(row, "content", "replaced after digest")
        return result

    monkeypatch.setattr(mod.OfflineContextPreview, "__getattribute__", late_swap)
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _preview(row)


def test_last_authority_getter_cannot_mutate_record_ids(monkeypatch):
    original = mod.OfflineContextPreview.__getattribute__

    def late_swap(self, name):
        result = original(self, name)
        if name == "retention_authorized":
            object.__setattr__(self, "record_ids", ("rec_" + "f" * 32,))
        return result

    monkeypatch.setattr(mod.OfflineContextPreview, "__getattribute__", late_swap)
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _preview(_fixture())
