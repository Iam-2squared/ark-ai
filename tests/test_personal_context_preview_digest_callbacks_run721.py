"""Synthetic Personal Context never forwards private fixtures to rebound hash/JSON.

No real profile, consent, user Memory or external dispatch is involved.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import personal_context_offline_preview as preview

OWNER = "a" * 64
SCOPE = "b" * 64


def _fixture():
    content = "synthetic private context fixture"
    return preview.OfflineContextFixture(
        "rec_" + "1" * 32, OWNER, SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 2000,
    )


def _build(row):
    return preview.build_offline_context_preview(
        (row,), owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,), observed_at_ms=1000,
    )


@pytest.mark.parametrize("callback", ("sha256", "dumps", "loads"))
@pytest.mark.parametrize("operation", ("build", "verify"))
def test_rebound_digest_or_json_callback_denied_before_private_preview(
    monkeypatch, callback, operation,
):
    row = _fixture()
    report = _build(row)
    calls = []

    def rogue(*_args, **_kwargs):
        calls.append("private data")
        pytest.fail("rebound callback must not receive private fixture")

    with monkeypatch.context() as patch:
        if callback == "sha256":
            patch.setattr(preview.hashlib, "sha256", rogue)
        else:
            patch.setattr(preview.json, callback, rogue)

        with pytest.raises(
            preview.OfflineContextPreviewRejected,
            match="authority definition changed",
        ):
            if operation == "build":
                _build(row)
            else:
                preview.verify_offline_context_preview(
                    report, (row,), owner_digest=OWNER,
                    allowed_scope_digests=(SCOPE,), observed_at_ms=1000,
                    retained_local_digest=report.local_digest,
                )
    assert calls == []
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False
