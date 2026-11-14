"""Privacy redaction must reject hostile class descriptors before calling them.

Synthetic fully masked text only; no owner consent, deletion, or real export.
"""

import hashlib

import pytest

from ark import offline_context_redaction as redaction


class FakeClassProperty:
    def __init__(self, original, calls):
        self.original = original
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("executed")
        return self.original if instance is None else False


def _request():
    raw = "synthetic secret"
    return dict(
        text=raw,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, len(raw), "SECRET"),),
    )


@pytest.mark.parametrize("flag", redaction._DENIAL_NAMES)
def test_preinstalled_class_descriptor_is_never_executed(
    monkeypatch, flag,
):
    request = _request()
    invoked = []
    original = vars(redaction.RedactedOfflinePreview)[flag]
    monkeypatch.setattr(
        redaction.RedactedOfflinePreview,
        flag,
        FakeClassProperty(original, invoked),
    )

    def forbidden_hash(*_args, **_kwargs):
        raise AssertionError("private fixture read before permission preflight")

    monkeypatch.setattr(redaction.hashlib, "sha256", forbidden_hash)
    with pytest.raises(
        redaction.OfflineRedactionRejected,
        match="authority definition changed",
    ):
        redaction.preview_offline_redaction(**request)
    assert invoked == []


@pytest.mark.parametrize("flag", redaction._DENIAL_NAMES)
def test_late_class_descriptor_is_never_executed(monkeypatch, flag):
    request = _request()
    invoked = []
    original = vars(redaction.RedactedOfflinePreview)[flag]
    sha256 = redaction.hashlib.sha256

    def install_after_source_hash(payload=b""):
        monkeypatch.setattr(
            redaction.RedactedOfflinePreview,
            flag,
            FakeClassProperty(original, invoked),
        )
        return sha256(payload)

    monkeypatch.setattr(redaction.hashlib, "sha256", install_after_source_hash)
    with pytest.raises(
        redaction.OfflineRedactionRejected,
        match="authority definition changed",
    ):
        redaction.preview_offline_redaction(**request)
    assert invoked == []


def test_full_mask_still_returns_inert_non_exportable_preview():
    report = redaction.preview_offline_redaction(**_request())
    assert report.complete_masking is True
    assert report.masked_text == "[MASK:SECRET]"
    assert report.consent_verified is False
    assert report.privacy_erasure_proven is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
