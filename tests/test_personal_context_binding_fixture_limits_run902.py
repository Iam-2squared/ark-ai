"""Privacy-safe request-binding parser and record-shape adversarial fixtures.

All context strings are synthetic, local and non-identifying. A rehashed
fixture never asserts consent, live revocation freshness or external export.
"""

import hashlib
import json
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

_REQUEST = "ctxreq_" + "1" * 64
_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "2" * 32
_DOMAIN = b"ARK-local-context-fixture-preview-v1\0"


def _preview():
    content = "synthetic private fixture"
    fixture = OfflineContextFixture(
        _RECORD, _OWNER, _SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 1000,
    )
    return build_offline_context_preview(
        (fixture,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=100,
    )


def _rewritten(preview, payload):
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    )
    digest = hashlib.sha256(_DOMAIN + canonical.encode("utf-8")).hexdigest()
    return replace(
        preview, canonical_local_json=canonical, local_digest=digest,
    )


def _not_authorized(binding):
    assert binding.consent_verified is False
    assert binding.revocation_freshness_verified is False
    assert binding.external_export_authorized is False
    assert binding.tool_dispatch_authorized is False
    assert binding.retention_authorized is False


def test_multibyte_canonical_byte_budget_blocks_before_private_json_parse():
    preview = _preview()
    # The character count is below the v1 65,536 limit, but the encoded
    # payload is over budget; this must be detected before json.loads.
    oversized = replace(preview, canonical_local_json="🌱" * 17_000)
    with pytest.raises(OfflineContextBindingRejected, match="byte budget"):
        bind_offline_context_request(_REQUEST, oversized)


def test_unpaired_surrogate_in_serialized_private_text_is_bounded():
    preview = _preview()
    corrupted = replace(preview, canonical_local_json="\ud800")
    with pytest.raises(OfflineContextBindingRejected, match="JSON invalid"):
        bind_offline_context_request(_REQUEST, corrupted)


@pytest.mark.parametrize(
    "payload_mutation",
    [
        lambda value: value["records"][0].update(content={"unexpected": "text"}),
        lambda value: value["records"][0].update(scope_digest="wrong"),
        lambda value: value["records"][0].update(record_id="rec_" + "3" * 32),
        lambda value: value["records"].append(value["records"][0]),
    ],
)
def test_rehashed_but_structurally_invalid_record_never_grants_export(
    payload_mutation,
):
    preview = _preview()
    payload = json.loads(preview.canonical_local_json)
    payload_mutation(payload)
    forged = _rewritten(preview, payload)
    with pytest.raises(OfflineContextBindingRejected):
        bind_offline_context_request(_REQUEST, forged)


def test_rehashed_valid_fixture_is_still_not_consent_or_freshness_proof():
    preview = _preview()
    payload = json.loads(preview.canonical_local_json)
    payload["records"][0]["content"] = "other synthetic fixture only"
    forged = _rewritten(preview, payload)
    receipt = bind_offline_context_request(_REQUEST, forged)
    _not_authorized(receipt)
    assert receipt.context_digest != preview.local_digest
    assert "other synthetic fixture only" not in repr(receipt)
