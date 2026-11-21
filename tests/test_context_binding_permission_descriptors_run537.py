"""Offline Personal Context binding cannot mint authority via reentrant getters."""

from __future__ import annotations

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
    content = "synthetic private fixture"
    record = OfflineContextFixture(
        "rec_" + "2" * 32, _OWNER, _SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 1000,
    )
    return build_offline_context_preview(
        (record,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
    )


@pytest.mark.parametrize("earlier", (
    "consent_verified", "revocation_freshness_verified",
    "external_export_authorized", "tool_dispatch_authorized",
))
def test_last_false_binding_getter_cannot_rebind_earlier_denial(
    monkeypatch, earlier,
):
    def rebind(_self):
        monkeypatch.setattr(
            binding.OfflineContextRequestBinding, earlier,
            property(lambda _other: False),
        )
        return False

    monkeypatch.setattr(
        binding.OfflineContextRequestBinding, "retention_authorized",
        property(rebind),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="changed"):
        binding.bind_offline_context_request(_REQUEST, _preview())


@pytest.mark.parametrize("earlier", (
    "consent_verified", "external_export_authorized",
))
def test_last_false_preview_getter_cannot_rebind_earlier_denial(
    monkeypatch, earlier,
):
    preview_receipt = _preview()  # Construct before monkeypatching a preview denial.

    def rebind(_self):
        monkeypatch.setattr(
            binding._PREVIEW_TYPE, earlier, property(lambda _other: False),
        )
        return False

    monkeypatch.setattr(
        binding._PREVIEW_TYPE, "retention_authorized", property(rebind),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="changed"):
        binding.bind_offline_context_request(_REQUEST, preview_receipt)


def test_last_false_binding_getter_cannot_replace_equal_receipt_digest(
    monkeypatch,
):
    def replace_digest(self):
        original = self.binding_digest
        clone = ("!" + original)[1:]
        assert clone == original and clone is not original
        object.__setattr__(self, "binding_digest", clone)
        return False

    monkeypatch.setattr(
        binding.OfflineContextRequestBinding, "retention_authorized",
        property(replace_digest),
    )
    with pytest.raises(binding.OfflineContextBindingRejected, match="changed"):
        binding.bind_offline_context_request(_REQUEST, _preview())


def test_honest_binding_remains_deterministic_and_never_authorizing():
    preview = _preview()
    first = binding.bind_offline_context_request(_REQUEST, preview)
    second = binding.bind_offline_context_request(_REQUEST, preview)
    assert first == second
    assert first.record_count == 1
    assert first.consent_verified is False
    assert first.revocation_freshness_verified is False
    assert first.external_export_authorized is False
    assert first.tool_dispatch_authorized is False
    assert first.retention_authorized is False
    assert "synthetic private fixture" not in repr(first)
