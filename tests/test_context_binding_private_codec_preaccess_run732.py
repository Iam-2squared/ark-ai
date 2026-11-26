"""Personal Context request binding must never disclose private text to forged codecs.

Synthetic fixtures only; no real records, consent, external providers, or tools.
"""

import hashlib

import pytest

from ark import personal_context_request_binding as binding
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

OWNER = "a" * 64
SCOPE = "b" * 64
RECORD = "rec_" + "c" * 32
REQUEST = "ctxreq_" + "d" * 64
PRIVATE_TEXT = "synthetic private canary"


def _source():
    fixture = OfflineContextFixture(
        RECORD, OWNER, SCOPE, PRIVATE_TEXT,
        hashlib.sha256(PRIVATE_TEXT.encode("utf-8")).hexdigest(), 1000,
    )
    return build_offline_context_preview(
        (fixture,), owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,), observed_at_ms=100,
    )


@pytest.mark.parametrize("change", (
    "sha256", "json_loads", "json_dumps", "hashlib_module",
    "json_module", "re_module", "compile", "preview_domain",
    "binding_domain", "sha_regex", "request_regex", "record_regex",
))
def test_preinstalled_private_codec_or_parser_must_refuse_without_callback(
    monkeypatch, change,
):
    preview = _source()
    seen = []

    def hostile(*args, **kwargs):
        seen.append("private input exposed")
        raise AssertionError("forged context codec called")

    if change == "sha256":
        monkeypatch.setattr(binding.hashlib, "sha256", hostile)
    elif change == "json_loads":
        monkeypatch.setattr(binding.json, "loads", hostile)
    elif change == "json_dumps":
        monkeypatch.setattr(binding.json, "dumps", hostile)
    elif change == "hashlib_module":
        monkeypatch.setattr(binding, "hashlib", object())
    elif change == "json_module":
        monkeypatch.setattr(binding, "json", object())
    elif change == "re_module":
        monkeypatch.setattr(binding, "re", object())
    elif change == "compile":
        monkeypatch.setattr(binding.re, "compile", hostile)
    elif change.endswith("_domain"):
        name = "_PREVIEW_DOMAIN" if change == "preview_domain" else "_BINDING_DOMAIN"
        # Equal value but a different bytes carrier is a different review epoch.
        monkeypatch.setattr(binding, name, bytes(bytearray(getattr(binding, name))))
    else:
        name = {"sha_regex": "_SHA", "request_regex": "_REQUEST",
                "record_regex": "_RECORD"}[change]
        class FakeRegex:
            def fullmatch(self, private):
                hostile(private)
        monkeypatch.setattr(binding, name, FakeRegex())

    try:
        with pytest.raises(binding.OfflineContextBindingRejected) as exc:
            binding.bind_offline_context_request(REQUEST, preview)
    finally:
        # Restore replacements before pytest's own exception formatting and
        # assertion helpers potentially consult global json/re/hashlib.
        monkeypatch.undo()
    assert "codec changed" in str(exc.value)
    assert seen == []


def test_original_binding_remains_deterministic_and_denies_every_authority():
    preview = _source()
    first = binding.bind_offline_context_request(REQUEST, preview)
    second = binding.bind_offline_context_request(REQUEST, preview)
    assert first == second
    assert first.record_count == 1
    assert first.context_digest == preview.local_digest
    assert first.consent_verified is False
    assert first.revocation_freshness_verified is False
    assert first.external_export_authorized is False
    assert first.tool_dispatch_authorized is False
    assert first.retention_authorized is False
    assert PRIVATE_TEXT not in repr(first)
