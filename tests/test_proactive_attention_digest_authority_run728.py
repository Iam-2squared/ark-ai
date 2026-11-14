"""Proactive offline attention never invokes substituted digest/JSON authority.

Every input is synthetic and no notification, tool, consent or trusted clock
is exposed by this preview.
"""

from __future__ import annotations

import re

import pytest

from ark import proactive_attention_preview as attention


@pytest.mark.parametrize("target", (
    "hash", "json_dumps", "hash_module", "json_module",
    "digest_domain", "sha_pattern", "time_bound", "marker_budget",
))
def test_preinstalled_callback_or_protocol_drift_refused_before_access(
    monkeypatch, target,
):
    policy = attention.AttentionBudgetPolicy(
        "a" * 64, "b" * 64, 10, 100, 2, False,
    )
    marker = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "c" * 64, "d" * 64, 90,
    )
    calls = []

    def hostile(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted digest or JSON callback executed")

    if target == "hash":
        monkeypatch.setattr(attention.hashlib, "sha256", hostile)
    elif target == "json_dumps":
        monkeypatch.setattr(attention.json, "dumps", hostile)
    elif target == "hash_module":
        monkeypatch.setattr(attention, "hashlib", object())
    elif target == "json_module":
        monkeypatch.setattr(attention, "json", object())
    elif target == "digest_domain":
        monkeypatch.setattr(
            attention, "_DOMAIN", bytes(bytearray(attention._DOMAIN)),
        )
    elif target == "sha_pattern":
        monkeypatch.setattr(
            attention, "_SHA", re.compile(r"[0-9a-fA-F]{64}\Z"),
        )
    elif target == "time_bound":
        monkeypatch.setattr(attention, "_MAX_MS", attention._MAX_MS + 1)
    else:
        monkeypatch.setattr(attention, "_MAX_MARKERS", 257)

    with pytest.raises(
        attention.AttentionPreviewRejected,
        match="attention authority definition changed",
    ):
        attention.preview_proactive_attention(
            policy, (marker,),
            occurrence_sha256="e" * 64,
            observation_sha256="f" * 64,
            observed_now_ms=100,
        )
    assert calls == []


def test_unchanged_synthetic_attention_remains_no_action_or_notice():
    policy = attention.AttentionBudgetPolicy(
        "a" * 64, "b" * 64, 10, 100, 2, False,
    )
    marker = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "c" * 64, "d" * 64, 90,
    )
    result = attention.preview_proactive_attention(
        policy, (marker,),
        occurrence_sha256="e" * 64,
        observation_sha256="f" * 64,
        observed_now_ms=100,
    )
    assert result.disposition == "REVIEW_ONLY"
    assert result.notification_authorized is False
    assert result.action_authorized is False
    assert result.consent_verified is False
    assert result.trusted_clock_verified is False
