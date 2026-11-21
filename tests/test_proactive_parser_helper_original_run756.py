"""Offline proactive parsers cannot be swapped before synthetic review.

All fixtures are local digest labels and synthetic timestamps. No real
notification, authenticated time, consent, or execution is provided.
"""

from __future__ import annotations

import pytest

from ark import proactive_attention_preview as attention


def _review():
    policy = attention.AttentionBudgetPolicy(
        "a" * 64, "b" * 64, 10, 100, 2, False,
    )
    marker = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "c" * 64, "d" * 64, 90,
    )
    return attention.preview_proactive_attention(
        policy, (marker,),
        occurrence_sha256="e" * 64,
        observation_sha256="f" * 64,
        observed_now_ms=100,
    )


@pytest.mark.parametrize("helper", ("_sha", "_ms"))
@pytest.mark.parametrize("replacement", ("callable", "boolean", "noncallable"))
def test_replaced_synthetic_parser_refused_before_private_labels(
    monkeypatch, helper, replacement,
):
    calls = []

    def hostile(value):
        calls.append(value)
        raise AssertionError("untrusted helper received private fixture")

    if replacement == "callable":
        value = hostile
    elif replacement == "boolean":
        def always_true(_value):
            return True

        value = always_true
    else:
        value = object()
    monkeypatch.setattr(attention, helper, value)
    with pytest.raises(
        attention.AttentionPreviewRejected,
        match="attention authority definition changed",
    ):
        _review()
    assert calls == []


def test_original_parsers_preserve_denial_only_deterministic_review():
    first = _review()
    assert first == _review()
    assert first.disposition == "REVIEW_ONLY"
    assert first.notification_authorized is False
    assert first.action_authorized is False
    assert first.consent_verified is False
    assert first.trusted_clock_verified is False
