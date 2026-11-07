"""Synthetic Personal Context preview refuses substituted privacy authority.

The fixture contains dummy local text. This neither authenticates consent
nor authorizes model access, data export, retention or tool execution.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from ark import personal_context_offline_preview as mod


def _fixture():
    text = "local dummy context"
    return mod.OfflineContextFixture(
        "rec_" + "1" * 32, "a" * 64, "b" * 64, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 2000,
    )


def _preview(row):
    return mod.build_offline_context_preview(
        (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
    )


@pytest.mark.parametrize("flag", mod._PREVIEW_DENIAL_NAMES)
def test_false_only_privacy_property_rejected_before_content_hash(
    monkeypatch, flag,
):
    row = _fixture()
    calls = []

    def forbidden_hash(_data):
        calls.append(True)
        raise AssertionError("private fixture bytes must not be hashed")

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=forbidden_hash))
    monkeypatch.setattr(
        mod.OfflineContextPreview, flag, property(lambda _self: False),
    )
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _preview(row)
    assert calls == []


@pytest.mark.parametrize("flag", mod._PREVIEW_DENIAL_NAMES)
def test_reverification_rejects_privacy_swap_before_rebuilding(
    monkeypatch, flag,
):
    row = _fixture()
    report = _preview(row)
    rebuilt = []

    def forbidden_rebuild(*_args, **_kwargs):
        rebuilt.append(True)
        raise AssertionError("rebuild must not process private data")

    monkeypatch.setattr(
        mod, "build_offline_context_preview", forbidden_rebuild,
    )
    monkeypatch.setattr(
        mod.OfflineContextPreview, flag, property(lambda _self: False),
    )
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        mod.verify_offline_context_preview(
            report, (row,), owner_digest="a" * 64,
            allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
            retained_local_digest=report.local_digest,
        )
    assert rebuilt == []


def test_original_privacy_denials_are_passive_across_reverification():
    row = _fixture()
    report = _preview(row)
    assert mod.verify_offline_context_preview(
        report, (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
        retained_local_digest=report.local_digest,
    ) is None
    for flag in mod._PREVIEW_DENIAL_NAMES:
        assert getattr(report, flag) is False
