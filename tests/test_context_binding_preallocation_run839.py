"""Pre-allocation ingress budgets for private disconnected context receipts.

No live context, real user record, revocation claim, consent or network is used.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import (
    OfflineContextBindingRejected,
    bind_offline_context_request,
)

OWNER = "a" * 64
SCOPE = "b" * 64
ID = "rec_" + "c" * 32
REQUEST = "ctxreq_" + "1" * 64


def _fixture_preview():
    content = "synthetic only"
    item = OfflineContextFixture(
        ID, OWNER, SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 1000,
    )
    return build_offline_context_preview(
        (item,), owner_digest=OWNER, allowed_scope_digests=(SCOPE,),
        observed_at_ms=100,
    )


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("owner_digest", "a" * 100_000, "metadata"),
        ("record_ids", ("rec_" + "c" * 100_000,), "metadata"),
        ("local_digest", "d" * 100_000, "metadata"),
        ("canonical_local_json", "private" * 20_000, "byte budget"),
        ("canonical_local_json", "\ud800" * 70_000, "byte budget"),
    ],
)
def test_oversized_untrusted_preview_rejected_without_disclosure(field, value, error):
    forged = replace(_fixture_preview(), **{field: value})
    with pytest.raises(OfflineContextBindingRejected, match=error) as caught:
        bind_offline_context_request(REQUEST, forged)
    assert "private" not in str(caught.value)
    assert "rec_" not in str(caught.value)


@pytest.mark.parametrize("request", (
    "ctxreq_" + "a" * 100_000,
    "ctxreq_" + "\ud800" * 100,
))
def test_oversized_request_identifier_rejected_before_private_preview(request):
    preview = _fixture_preview()
    with pytest.raises(OfflineContextBindingRejected, match="request ID"):
        bind_offline_context_request(request, preview)


def test_canonical_preview_still_binds_without_authorizing_any_effect():
    report = bind_offline_context_request(REQUEST, _fixture_preview())
    assert report.record_count == 1
    assert report.consent_verified is False
    assert report.revocation_freshness_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False
