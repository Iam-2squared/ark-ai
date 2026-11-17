"""Private context fixture payloads stay out of diagnostics and denial paths.

Only synthetic strings are used; a valid offline preview is not consent,
profile persistence, permission to export or permission to execute a tool.
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
_SCOPE = "b" * 64
_OTHER_SCOPE = "c" * 64
_SECRET = "SYNTHETIC_PRIVATE_FIXTURE_DO_NOT_PRINT_938"


def _fixture() -> OfflineContextFixture:
    return OfflineContextFixture(
        "rec_" + "d" * 32, _OWNER, _SCOPE, _SECRET,
        hashlib.sha256(_SECRET.encode("utf-8")).hexdigest(), 200,
    )


def test_valid_context_preview_is_private_in_reprs_and_never_authorizes() -> None:
    fixture = _fixture()
    report = build_offline_context_preview(
        (fixture,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
    )
    verify_offline_context_preview(
        report, (fixture,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
        retained_local_digest=report.local_digest,
    )
    assert _SECRET not in repr(fixture)
    assert _SECRET not in repr(report)
    assert _SECRET in report.canonical_local_json
    assert report.record_ids == (fixture.record_id,)
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False


@pytest.mark.parametrize("invalid", ("digest", "scope", "expired"))
def test_invalid_context_batch_rejects_without_content_in_exception(
    invalid: str,
) -> None:
    original = _fixture()
    if invalid == "digest":
        fixture = replace(original, content_sha256="0" * 64)
    elif invalid == "scope":
        fixture = replace(original, scope_digest=_OTHER_SCOPE)
    else:
        fixture = replace(original, expires_at_ms=100)
    with pytest.raises(OfflineContextPreviewRejected) as rejection:
        build_offline_context_preview(
            (fixture,), owner_digest=_OWNER,
            allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
        )
    assert _SECRET not in str(rejection.value)
    assert _SECRET not in repr(rejection.value)
    assert _SECRET not in repr(fixture)
