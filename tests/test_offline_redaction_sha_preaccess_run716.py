"""Reject unreviewed digest callbacks before synthetic private masking data.

No actual personal context, file, external account, or export is involved.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_redaction as redaction


@pytest.mark.parametrize("complete", [True, False])
def test_replaced_sha_never_receives_private_fixture_bytes(
    monkeypatch, complete,
):
    source = "synthetic private fixture"
    retained_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    full = (redaction.OfflineRedactionSpan(0, len(source), "SECRET"),)
    partial = (redaction.OfflineRedactionSpan(0, 9, "SECRET"),)
    received = []

    def hostile_sha(data=b""):
        received.append(data)
        raise AssertionError("private bytes leaked to substituted digest")

    # Build every fixture and retained digest before patching shared hashlib.
    with monkeypatch.context() as patch:
        patch.setattr(redaction.hashlib, "sha256", hostile_sha)
        with pytest.raises(
            redaction.OfflineRedactionRejected,
            match="masked preview authority definition changed",
        ):
            redaction.preview_offline_redaction(
                source,
                owner_digest="a" * 64,
                scope_digest="b" * 64,
                retained_source_sha256=retained_sha,
                spans=full if complete else partial,
                require_complete=complete,
            )
    assert received == []


def test_original_sha_still_produces_non_authorizing_mask():
    source = "synthetic private fixture"
    preview = redaction.preview_offline_redaction(
        source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, len(source), "SECRET"),),
    )
    assert preview.masked_text == "[MASK:SECRET]"
    assert preview.consent_verified is False
    assert preview.external_export_authorized is False
