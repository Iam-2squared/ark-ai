"""Disconnected attention diagnostics reject executable result constructors.

Synthetic-only policy and clock; no actual notification or tool dispatch.
"""

from __future__ import annotations

import pytest

from ark import proactive_attention_preview as attention

SCOPE = "a" * 64
TRIGGER = "b" * 64


def _preview():
    policy = attention.AttentionBudgetPolicy(
        SCOPE, TRIGGER, 1, 100, 1, False,
    )
    return attention.preview_proactive_attention(
        policy, (),
        occurrence_sha256="c" * 64,
        observation_sha256="d" * 64,
        observed_now_ms=100,
    )


@pytest.mark.parametrize("stage", ("preinstalled", "digest_callback"))
def test_forged_result_init_rejected_before_execution(monkeypatch, stage):
    constructed = []

    def injected(self, *args):
        constructed.append(args)

    if stage == "preinstalled":
        monkeypatch.setattr(attention.AttentionBudgetPreview, "__init__", injected)
    else:
        original_hash = attention.hashlib.sha256

        def corrupt_on_digest(payload):
            monkeypatch.setattr(
                attention.AttentionBudgetPreview, "__init__", injected,
            )
            return original_hash(payload)

        monkeypatch.setattr(attention.hashlib, "sha256", corrupt_on_digest)

    with pytest.raises(
        attention.AttentionPreviewRejected, match="authority definition changed",
    ):
        _preview()
    assert constructed == []


def test_clean_attention_preview_is_still_deny_only():
    result = _preview()
    assert type(result) is attention.AttentionBudgetPreview
    assert result.disposition == "REVIEW_ONLY"
    assert result.notification_authorized is False
    assert result.action_authorized is False
    assert result.consent_verified is False
    assert result.trusted_clock_verified is False
