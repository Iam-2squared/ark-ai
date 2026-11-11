"""Original privacy-preview validation names must remain authoritative."""

from __future__ import annotations

import hashlib

import pytest

from ark import personal_context_offline_preview as mod


def _inputs():
    content = "private local fixture"
    fixture = mod.OfflineContextFixture(
        record_id="rec_" + "a" * 32,
        owner_digest="b" * 64,
        scope_digest="c" * 64,
        content=content,
        content_sha256=hashlib.sha256(content.encode()).hexdigest(),
        expires_at_ms=1000,
    )
    return (fixture,), "b" * 64, ("c" * 64,), 100


@pytest.mark.parametrize(("control", "value"), (
    ("_FIXTURE_FIELDS", ("record_id",)),
    ("_RESULT_FIELDS", ("local_digest",)),
    ("_CARRIER_HOOKS", ()),
    ("_PREVIEW_DENIAL_NAMES", ("consent_verified",)),
))
def test_changed_name_control_denied_before_private_preview(monkeypatch, control, value):
    fixtures, owner, scopes, now = _inputs()
    with monkeypatch.context() as patch:
        patch.setattr(mod, control, value)
        with pytest.raises(mod.OfflineContextPreviewRejected, match="authority definition"):
            mod.build_offline_context_preview(
                fixtures, owner_digest=owner,
                allowed_scope_digests=scopes, observed_at_ms=now,
            )
    valid = mod.build_offline_context_preview(
        fixtures, owner_digest=owner,
        allowed_scope_digests=scopes, observed_at_ms=now,
    )
    assert valid.external_export_authorized is False
    assert valid.tool_dispatch_authorized is False


@pytest.mark.parametrize(("control", "value"), (
    ("_FIXTURE_FIELDS", ()),
    ("_RESULT_FIELDS", ()),
    ("_CARRIER_HOOKS", ("__init__",)),
    ("_PREVIEW_DENIAL_NAMES", ("retention_authorized",)),
))
def test_changed_name_control_denied_before_verify_rebuild(monkeypatch, control, value):
    fixtures, owner, scopes, now = _inputs()
    report = mod.build_offline_context_preview(
        fixtures, owner_digest=owner,
        allowed_scope_digests=scopes, observed_at_ms=now,
    )
    with monkeypatch.context() as patch:
        patch.setattr(mod, control, value)
        with pytest.raises(mod.OfflineContextPreviewRejected, match="authority definition"):
            mod.verify_offline_context_preview(
                report, fixtures, owner_digest=owner,
                allowed_scope_digests=scopes, observed_at_ms=now,
                retained_local_digest=report.local_digest,
            )
    mod.verify_offline_context_preview(
        report, fixtures, owner_digest=owner,
        allowed_scope_digests=scopes, observed_at_ms=now,
        retained_local_digest=report.local_digest,
    )
