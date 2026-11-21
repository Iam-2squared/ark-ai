"""Bounded private context parser cannot leak raw recursion exceptions."""

from __future__ import annotations

import hashlib

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreview,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import (
    OfflineContextBindingRejected,
    bind_offline_context_request,
)

_OWNER = "a" * 64
_RECORD = "rec_" + "b" * 32
_SCOPE = "c" * 64
_REQUEST = "ctxreq_" + "d" * 64


@pytest.mark.parametrize("depth", [900, 1100, 2500, 4000])
def test_private_preview_deep_json_fails_closed(depth: int) -> None:
    canonical = (
        '{"owner_digest":"' + _OWNER + '","records":'
        + "[" * depth + "0" + "]" * depth + "}"
    )
    assert len(canonical.encode("utf-8")) < 65_536
    fixture_preview = OfflineContextPreview(
        _OWNER, (_RECORD,), canonical, "e" * 64,
    )
    with pytest.raises(OfflineContextBindingRejected):
        bind_offline_context_request(_REQUEST, fixture_preview)


def test_private_context_normal_fixture_remains_local_and_denied() -> None:
    fixture = OfflineContextFixture(
        _RECORD, _OWNER, _SCOPE, "local private content",
        hashlib.sha256(b"local private content").hexdigest(), 100,
    )
    preview = build_offline_context_preview(
        (fixture,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=5,
    )
    binding = bind_offline_context_request(_REQUEST, preview)
    assert binding.record_count == 1
    assert binding.owner_digest == _OWNER
    assert binding.consent_verified is False
    assert binding.revocation_freshness_verified is False
    assert binding.external_export_authorized is False
    assert binding.tool_dispatch_authorized is False
    assert binding.retention_authorized is False
    assert "local private content" not in repr(binding)
