"""Retained private context evidence must not be rewritten during local rebuild.

No live account, consent inference, external export or backend dispatch.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import personal_context_offline_preview as context


@pytest.mark.parametrize("attack", ("repair_forged_digest", "replace_equal_ids"))
def test_reentrant_hash_cannot_change_retained_preview_during_verification(
    monkeypatch, attack,
):
    private_text = "isolated synthetic context"
    fixture = context.OfflineContextFixture(
        "rec_" + "4" * 32,
        "a" * 64,
        "b" * 64,
        private_text,
        hashlib.sha256(private_text.encode()).hexdigest(),
        2000,
    )
    expected = context.build_offline_context_preview(
        (fixture,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
    )
    if attack == "repair_forged_digest":
        report = context.OfflineContextPreview(
            expected.owner_digest, expected.record_ids,
            expected.canonical_local_json, "f" * 64,
        )
    else:
        report = expected
    original_hash = context.hashlib.sha256
    injected = []

    def digest(payload=b""):
        if payload == private_text.encode() and not injected:
            injected.append(attack)
            if attack == "repair_forged_digest":
                object.__setattr__(report, "local_digest", expected.local_digest)
            else:
                alias = tuple(list(report.record_ids))
                assert alias == report.record_ids
                assert alias is not report.record_ids
                object.__setattr__(report, "record_ids", alias)
        return original_hash(payload)

    monkeypatch.setattr(context.hashlib, "sha256", digest)
    with pytest.raises(
        context.OfflineContextPreviewRejected,
        match="context preview authority definition changed",
    ):
        context.verify_offline_context_preview(
            report, (fixture,), owner_digest="a" * 64,
            allowed_scope_digests=("b" * 64,), observed_at_ms=1000,
            retained_local_digest=expected.local_digest,
        )
    # A rebound digest function must never see private fixture bytes or mutate
    # a retained report, even when the old later-stage check could catch it.
    assert injected == []
    if attack == "repair_forged_digest":
        assert report.local_digest == "f" * 64
    else:
        assert report.record_ids is expected.record_ids


def test_unchanged_retained_private_report_remains_verifiable():
    text = "synthetic context only"
    fixture = context.OfflineContextFixture(
        "rec_" + "5" * 32, "c" * 64, "d" * 64, text,
        hashlib.sha256(text.encode()).hexdigest(), 2000,
    )
    report = context.build_offline_context_preview(
        (fixture,), owner_digest="c" * 64,
        allowed_scope_digests=("d" * 64,), observed_at_ms=1000,
    )
    context.verify_offline_context_preview(
        report, (fixture,), owner_digest="c" * 64,
        allowed_scope_digests=("d" * 64,), observed_at_ms=1000,
        retained_local_digest=report.local_digest,
    )
    assert report.consent_verified is False
    assert report.external_export_authorized is False
