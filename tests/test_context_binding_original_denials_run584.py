"""Original denial-only Personal Context descriptors are immutable inputs.

Synthetic private fixture data only; a hash-bound preview never grants
consent, export, retention, live revocation authority or tool execution.
"""

import hashlib

import pytest

import ark.personal_context_request_binding as binding
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

_REQUEST = "ctxreq_" + "1" * 64
_OWNER = "a" * 64
_SCOPE = "b" * 64


def _preview():
    content = "offline fake context"
    fixture = OfflineContextFixture(
        "rec_" + "2" * 32,
        _OWNER,
        _SCOPE,
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        1000,
    )
    return build_offline_context_preview(
        (fixture,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=100,
    )


@pytest.mark.parametrize("name", (
    "consent_verified",
    "external_export_authorized",
    "tool_dispatch_authorized",
    "retention_authorized",
))
def test_preinstalled_false_preview_descriptor_is_not_an_original_witness(
    monkeypatch, name,
):
    preview = _preview()
    monkeypatch.setattr(
        binding._PREVIEW_TYPE, name, property(lambda _self: False),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="preview carrier changed"):
        binding.bind_offline_context_request(_REQUEST, preview)


@pytest.mark.parametrize("name", (
    "consent_verified",
    "revocation_freshness_verified",
    "external_export_authorized",
    "tool_dispatch_authorized",
    "retention_authorized",
))
def test_preinstalled_false_binding_descriptor_cannot_become_baseline(
    monkeypatch, name,
):
    preview = _preview()
    monkeypatch.setattr(
        binding._BINDING_TYPE, name, property(lambda _self: False),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="binding changed"):
        binding.bind_offline_context_request(_REQUEST, preview)


def test_original_private_binding_is_deterministic_and_denial_only():
    preview = _preview()
    result = binding.bind_offline_context_request(_REQUEST, preview)
    assert result.record_count == 1
    assert result.consent_verified is False
    assert result.revocation_freshness_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.retention_authorized is False
    assert "offline fake context" not in repr(result)
