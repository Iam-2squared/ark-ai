"""No-content, request-bound Personal Context fixture custody regressions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

import ark.personal_context_request_binding as binding
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

_REQUEST = "ctxreq_" + "1" * 64
_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "2" * 32


def _preview(content="private fixture"):
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


def test_request_binding_is_deterministic_and_private():
    preview = _preview("日本語 private content")
    first = binding.bind_offline_context_request(_REQUEST, preview)
    assert first == binding.bind_offline_context_request(_REQUEST, preview)
    assert first.record_count == 1
    assert first.context_digest == preview.local_digest
    assert len(first.binding_digest) == 64
    assert "private content" not in repr(first)
    assert first.consent_verified is False
    assert first.revocation_freshness_verified is False
    assert first.external_export_authorized is False
    assert first.tool_dispatch_authorized is False
    assert first.retention_authorized is False


def test_same_context_cannot_reuse_request_bound_digest():
    preview = _preview()
    first = binding.bind_offline_context_request(_REQUEST, preview)
    second = binding.bind_offline_context_request(
        "ctxreq_" + "3" * 64, preview,
    )
    assert first.context_digest == second.context_digest
    assert first.binding_digest != second.binding_digest


@pytest.mark.parametrize("request_id", [
    None, True, "ctxreq_" + "f" * 63, "act_" + "a" * 64,
    "ctxreq_" + "g" * 64,
])
def test_invalid_request_identity_rejected(request_id):
    with pytest.raises(binding.OfflineContextBindingRejected, match="request ID"):
        binding.bind_offline_context_request(request_id, _preview())


@pytest.mark.parametrize("mutation", [
    {"local_digest": "f" * 64},
    {"record_ids": ("rec_" + "f" * 32,)},
    {"owner_digest": "d" * 64},
])
def test_preview_claim_retargeting_is_denied(mutation):
    forged = replace(_preview(), **mutation)
    with pytest.raises(binding.OfflineContextBindingRejected):
        binding.bind_offline_context_request(_REQUEST, forged)


def test_rehashed_json_with_changed_scope_is_not_original_scope():
    preview = _preview()
    payload = json.loads(preview.canonical_local_json)
    payload["records"][0]["scope_digest"] = "f" * 64
    canonical = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        allow_nan=False, separators=(",", ":"),
    )
    local_digest = hashlib.sha256(
        binding._PREVIEW_DOMAIN + canonical.encode("utf-8"),
    ).hexdigest()
    # The original v1 preview fields cannot authenticate source or consent:
    # a fully rewritten fixture with recomputed digest is still untrusted.
    forged = replace(
        preview, canonical_local_json=canonical, local_digest=local_digest,
    )
    report = binding.bind_offline_context_request(_REQUEST, forged)
    assert report.tool_dispatch_authorized is False
    assert report.revocation_freshness_verified is False


def test_malformed_noncanonical_json_is_denied():
    preview = _preview()
    forged = replace(
        preview,
        canonical_local_json=preview.canonical_local_json + " ",
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="identity mismatch"):
        binding.bind_offline_context_request(_REQUEST, forged)


def test_preview_changed_during_parse_is_denied(monkeypatch):
    preview = _preview()
    original = binding.json.loads

    def mutate(serialized):
        decoded = original(serialized)
        object.__setattr__(preview, "owner_digest", "c" * 64)
        return decoded

    monkeypatch.setattr(binding.json, "loads", mutate)
    with pytest.raises(binding.OfflineContextBindingRejected, match="carrier changed"):
        binding.bind_offline_context_request(_REQUEST, preview)


def test_preview_authority_forgery_is_denied(monkeypatch):
    preview = _preview()
    monkeypatch.setattr(
        type(preview), "consent_verified", property(lambda self: True),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="carrier changed"):
        binding.bind_offline_context_request(_REQUEST, preview)


def test_forged_result_type_cannot_claim_external_authority(monkeypatch):
    preview = _preview()
    monkeypatch.setattr(
        binding, "OfflineContextRequestBinding", lambda *args: object(),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="binding changed"):
        binding.bind_offline_context_request(_REQUEST, preview)


def test_oversize_serialized_preview_denied_without_disclosure():
    preview = _preview()
    forged = replace(preview, canonical_local_json="A" * 65_537)
    with pytest.raises(binding.OfflineContextBindingRejected, match="byte budget"):
        binding.bind_offline_context_request(_REQUEST, forged)
