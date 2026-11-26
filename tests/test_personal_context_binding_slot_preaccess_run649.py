"""Synthetic request binding pins private preview and result carrier slots.

Import-original field identity is checked before reading fixture JSON. The
content-free binding remains neither consent nor a live revocation check.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.personal_context_request_binding as binding
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

_REQUEST = "ctxreq_" + "1" * 64


def _preview():
    content = "private fixture 日本語"
    fixture = OfflineContextFixture(
        "rec_" + "2" * 32, "a" * 64, "b" * 64,
        content, hashlib.sha256(content.encode()).hexdigest(), 1000,
    )
    return build_offline_context_preview(
        (fixture,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )


@pytest.mark.parametrize(("which", "name"), [
    ("preview", "owner_digest"),
    ("preview", "record_ids"),
    ("preview", "canonical_local_json"),
    ("preview", "local_digest"),
    ("result", "request_id"),
    ("result", "owner_digest"),
    ("result", "context_digest"),
    ("result", "record_count"),
    ("result", "binding_digest"),
    ("preview", "__getattribute__"),
    ("result", "__getattribute__"),
    ("preview", "__getattr__"),
    ("result", "__getattr__"),
])
def test_preinstalled_executable_carrier_slot_rejected_before_access(
    monkeypatch, which, name,
):
    preview = _preview()
    invoked = []

    def forbidden(*_args):
        invoked.append(name)
        raise AssertionError("no substituted accessor should be called")

    klass = binding._PREVIEW_TYPE if which == "preview" else binding._BINDING_TYPE
    with monkeypatch.context() as patch:
        if name.startswith("__"):
            patch.setattr(klass, name, forbidden, raising=False)
        else:
            patch.setattr(klass, name, property(forbidden))
        with pytest.raises(
            binding.OfflineContextBindingRejected,
            match="preview carrier changed|binding changed",
        ):
            binding.bind_offline_context_request(_REQUEST, preview)
    assert invoked == []


@pytest.mark.parametrize(("which", "name"), [
    ("preview", "canonical_local_json"),
    ("result", "binding_digest"),
])
def test_mutation_during_preview_json_parse_cannot_execute_slot(
    monkeypatch, which, name,
):
    preview = _preview()
    invoked = []
    parser_hits = []

    def forbidden(*_args):
        invoked.append(name)
        raise AssertionError("reentrant access forbidden")

    with monkeypatch.context() as patch:
        def mutate(serialized):
            parser_hits.append(serialized)
            raise AssertionError("private context passed to replaced JSON parser")

        patch.setattr(binding.json, "loads", mutate)
        with pytest.raises(
            binding.OfflineContextBindingRejected,
            match="private context binding codec changed",
        ):
            binding.bind_offline_context_request(_REQUEST, preview)
    assert parser_hits == []
    assert invoked == []


def test_original_request_remains_content_free_and_deny_only():
    result = binding.bind_offline_context_request(_REQUEST, _preview())
    assert result.record_count == 1
    assert "private fixture" not in repr(result)
    assert result.consent_verified is False
    assert result.revocation_freshness_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.retention_authorized is False
