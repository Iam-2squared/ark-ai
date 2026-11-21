"""Private local-only context fixtures must not execute forged dataclass accessors.

No personal account, Memory connector, export, user consent or backend call.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import personal_context_offline_preview as mod


def _case():
    content = "synthetic private context"
    row = mod.OfflineContextFixture(
        "rec_" + "1" * 32, "a" * 64, "b" * 64,
        content, hashlib.sha256(content.encode()).hexdigest(), 2000,
    )
    return row


def _build(row):
    return mod.build_offline_context_preview(
        (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
    )


def _verify(row, report, digest):
    mod.verify_offline_context_preview(
        report, (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
        retained_local_digest=digest,
    )


@pytest.mark.parametrize(
    "field",
    ("record_id", "owner_digest", "scope_digest", "content",
     "content_sha256", "expires_at_ms"),
)
def test_private_fixture_slot_spoof_refused_before_content_read(
    monkeypatch, field,
):
    row = _case()
    called: list[str] = []

    def attack(_self):
        called.append(field)
        raise AssertionError("private fixture accessor executed")

    monkeypatch.setattr(mod.OfflineContextFixture, field, property(attack))
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _build(row)
    assert called == []


@pytest.mark.parametrize(
    "field", ("owner_digest", "record_ids", "canonical_local_json", "local_digest"),
)
def test_retained_preview_slot_spoof_refused_before_private_read(
    monkeypatch, field,
):
    row = _case()
    result = _build(row)
    digest = result.local_digest
    called: list[str] = []

    def attack(_self):
        called.append(field)
        raise AssertionError("retained preview accessor executed")

    monkeypatch.setattr(mod.OfflineContextPreview, field, property(attack))
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _verify(row, result, digest)
    assert called == []


@pytest.mark.parametrize("target", ("fixture", "report"))
@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_lookup_hook_spoof_refused_before_private_access(
    monkeypatch, target, hook,
):
    row = _case()
    receipt = _build(row)
    digest = receipt.local_digest
    called: list[str] = []

    def attack(*_args, **_kwargs):
        called.append(hook)
        raise AssertionError("private lookup hook executed")

    cls = mod.OfflineContextFixture if target == "fixture" else mod.OfflineContextPreview
    monkeypatch.setattr(cls, hook, attack, raising=False)
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _verify(row, receipt, digest)
    assert called == []


def test_private_hash_callback_cannot_rebind_later_result_slot(monkeypatch):
    row = _case()
    called: list[str] = []
    original_sha256 = mod.hashlib.sha256

    def attack(_self):
        called.append("canonical_local_json")
        raise AssertionError("private report slot executed")

    def digest(payload=b""):
        if payload == b"synthetic private context":
            monkeypatch.setattr(
                mod.OfflineContextPreview, "canonical_local_json",
                property(attack),
            )
        return original_sha256(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", digest)
    with pytest.raises(
        mod.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        _build(row)
    assert called == []


def test_original_fixture_and_report_slots_preserve_local_verification():
    row = _case()
    receipt = _build(row)
    _verify(row, receipt, receipt.local_digest)
    assert receipt.consent_verified is False
    assert receipt.external_export_authorized is False
    assert receipt.tool_dispatch_authorized is False
    assert receipt.retention_authorized is False
