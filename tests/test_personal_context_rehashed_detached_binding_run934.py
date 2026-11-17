"""Detached Personal Context evidence must bind the original fixture bytes.

A locally recomputed self-consistent digest is not evidence of ownership or
consent. Synthetic-only inputs; no private Memory DB or external export.
"""

from __future__ import annotations

import hashlib
import json
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
_SECRET = "SYNTHETIC-SENSITIVE-CONTEXT-NO-USER-DATA"
_DOMAIN = b"ARK-local-context-fixture-preview-v1\\0"


def _fixture() -> OfflineContextFixture:
    return OfflineContextFixture(
        "rec_" + "1" * 32, _OWNER, _SCOPE, _SECRET,
        hashlib.sha256(_SECRET.encode()).hexdigest(), 2_000,
    )


@pytest.mark.parametrize(
    "mutation",
    ("owner", "scope", "record_id", "content", "extra_field", "empty_batch"),
)
def test_rehashed_detached_preview_cannot_rebind_original_fixture(
    mutation: str,
) -> None:
    fixtures = (_fixture(),)
    scopes = (_SCOPE, _OTHER_SCOPE)
    original = build_offline_context_preview(
        fixtures, owner_digest=_OWNER, allowed_scope_digests=scopes,
        observed_at_ms=1_000,
    )
    # This is an exact, valid fixture preview; its authority flags are false.
    assert verify_offline_context_preview(
        original, fixtures, owner_digest=_OWNER,
        allowed_scope_digests=scopes, observed_at_ms=1_000,
        retained_local_digest=original.local_digest,
    ) is None

    payload = json.loads(original.canonical_local_json)
    if mutation == "owner":
        payload["owner_digest"] = "d" * 64
    elif mutation == "scope":
        payload["records"][0]["scope_digest"] = _OTHER_SCOPE
    elif mutation == "record_id":
        payload["records"][0]["record_id"] = "rec_" + "2" * 32
    elif mutation == "content":
        payload["records"][0]["content"] = "altered-synthetic-content"
    elif mutation == "extra_field":
        payload["records"][0]["new_authority"] = True
    else:
        payload["records"] = []

    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    )
    digest = hashlib.sha256(_DOMAIN + canonical.encode("utf-8")).hexdigest()
    changed = replace(
        original, canonical_local_json=canonical, local_digest=digest,
    )
    assert digest != original.local_digest
    # Passing the new matching SHA defeats a weak digest-only check; the
    # detached report must still be compared with pinned original fixtures.
    with pytest.raises(OfflineContextPreviewRejected) as error:
        verify_offline_context_preview(
            changed, fixtures, owner_digest=_OWNER,
            allowed_scope_digests=scopes, observed_at_ms=1_000,
            retained_local_digest=digest,
        )
    assert _SECRET not in str(error.value)
    assert changed.external_export_authorized is False
    assert changed.tool_dispatch_authorized is False
