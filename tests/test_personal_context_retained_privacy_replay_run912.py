"""Synthetic Personal Context receipts remain deny-only after privacy state changes.

No live profile, consent, external export, credentials, Memory writes or
ToolBackend execution. A retained content digest cannot override a revoked
scope, expired fixture, different owner or changed local source record.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreviewRejected,
    build_offline_context_preview,
    verify_offline_context_preview,
)

_OWNER = "a" * 64
_OTHER = "b" * 64
_SCOPE = "c" * 64
_RECORD = "rec_" + "d" * 32
_CONTENT = "synthetic private context"
_EXPIRY = 5000


def _fixture() -> OfflineContextFixture:
    return OfflineContextFixture(
        _RECORD,
        _OWNER,
        _SCOPE,
        _CONTENT,
        hashlib.sha256(_CONTENT.encode("utf-8")).hexdigest(),
        _EXPIRY,
    )


def _retained():
    fixture = _fixture()
    report = build_offline_context_preview(
        (fixture,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
    )
    return fixture, report


@pytest.mark.parametrize(
    "change",
    (
        "scope_revoked",
        "owner_changed",
        "expires_now",
        "fixture_content_mutated",
        "fixture_hash_mutated",
        "retained_digest_replayed",
    ),
)
def test_retained_receipt_never_overrides_new_private_boundary(change: str) -> None:
    fixture, report = _retained()
    owner = _OWNER
    scopes = (_SCOPE,)
    now = 1000
    retained = report.local_digest

    if change == "scope_revoked":
        scopes = (_OTHER,)
    elif change == "owner_changed":
        owner = _OTHER
    elif change == "expires_now":
        now = _EXPIRY
    elif change == "fixture_content_mutated":
        fixture = replace(fixture, content=_CONTENT + "-changed")
    elif change == "fixture_hash_mutated":
        fixture = replace(fixture, content_sha256="e" * 64)
    elif change == "retained_digest_replayed":
        retained = "f" * 64

    with pytest.raises(OfflineContextPreviewRejected):
        verify_offline_context_preview(
            report,
            (fixture,),
            owner_digest=owner,
            allowed_scope_digests=scopes,
            observed_at_ms=now,
            retained_local_digest=retained,
        )

    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False


def test_unaltered_retained_preview_only_verifies_local_fixture() -> None:
    fixture, report = _retained()
    assert verify_offline_context_preview(
        report, (fixture,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
        retained_local_digest=report.local_digest,
    ) is None
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False
