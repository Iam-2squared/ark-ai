"""Synthetic private context preview refuses protocol drift before content access.

Retained local hashes are not user consent, authentic identity or permission
for model access, retention, tool dispatch or export.
"""

from __future__ import annotations

import hashlib
import re
from types import SimpleNamespace

import pytest

from ark import personal_context_offline_preview as preview


def _fixture():
    text = "synthetic local context"
    return preview.OfflineContextFixture(
        "rec_" + "1" * 32, "a" * 64, "b" * 64,
        text, hashlib.sha256(text.encode("utf-8")).hexdigest(), 2000,
    )


def _preview(row):
    return preview.build_offline_context_preview(
        (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
    )


@pytest.mark.parametrize("surface", (
    "hash_module", "json_module", "digest_pattern", "record_pattern",
    "domain", "time_ceiling", "record_ceiling", "content_ceiling",
    "total_ceiling", "serialized_ceiling",
))
@pytest.mark.parametrize("operation", ("build", "verify"))
def test_changed_privacy_contract_refused_before_synthetic_private_content(
    monkeypatch, surface, operation,
):
    row = _fixture()
    report = _preview(row)
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("synthetic private data")
        raise AssertionError("changed privacy callback executed")

    with monkeypatch.context() as patch:
        # A substituted module can claim the same basic callable name while
        # being an entirely new unreviewed implementation object.
        if surface == "hash_module":
            patch.setattr(preview, "hashlib", SimpleNamespace(sha256=forbidden))
        elif surface == "json_module":
            patch.setattr(
                preview, "json",
                SimpleNamespace(dumps=forbidden, loads=forbidden),
            )
        elif surface == "digest_pattern":
            patch.setattr(preview, "_DIGEST", re.compile(".*"))
        elif surface == "record_pattern":
            patch.setattr(preview, "_RECORD", re.compile(".*"))
        elif surface == "domain":
            patch.setattr(preview, "_DOMAIN", bytes(bytearray(preview._DOMAIN)))
        elif surface == "time_ceiling":
            patch.setattr(preview, "_MAX", preview._MAX - 1)
        elif surface == "record_ceiling":
            patch.setattr(preview, "_MAX_RECORDS", preview._MAX_RECORDS + 1)
        elif surface == "content_ceiling":
            patch.setattr(preview, "_MAX_CONTENT", preview._MAX_CONTENT + 1)
        elif surface == "total_ceiling":
            patch.setattr(preview, "_MAX_TOTAL", preview._MAX_TOTAL + 1)
        else:
            patch.setattr(
                preview, "_MAX_SERIALIZED_BYTES",
                preview._MAX_SERIALIZED_BYTES + 1,
            )
        with pytest.raises(
            preview.OfflineContextPreviewRejected,
            match="context preview authority definition changed",
        ):
            if operation == "build":
                _preview(row)
            else:
                preview.verify_offline_context_preview(
                    report, (row,), owner_digest="a" * 64,
                    allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
                    retained_local_digest=report.local_digest,
                )
    assert calls == []


def test_unmodified_private_context_local_preview_is_never_export_authority():
    row = _fixture()
    report = _preview(row)
    assert "synthetic local context" in report.canonical_local_json
    assert preview.verify_offline_context_preview(
        report, (row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
        retained_local_digest=report.local_digest,
    ) is None
    assert report.consent_verified is False
    assert report.retention_authorized is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
