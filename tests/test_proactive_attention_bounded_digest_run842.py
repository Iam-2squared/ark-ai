"""Synthetic proactive digest ingress stays fixed-width and notification-free.

No trusted time, real source, consent, notification, or external action is used.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import proactive_attention_preview as attention


def _policy() -> attention.AttentionBudgetPolicy:
    return attention.AttentionBudgetPolicy(
        "a" * 64, "b" * 64, 10, 1000, 2, False,
    )


def _review(
    policy: attention.AttentionBudgetPolicy,
    history: tuple[attention.SyntheticSurfaceMarker, ...] = (),
    *,
    occurrence: str = "c" * 64,
    observation: str = "d" * 64,
) -> attention.AttentionBudgetPreview:
    return attention.preview_proactive_attention(
        policy, history, occurrence_sha256=occurrence,
        observation_sha256=observation, observed_now_ms=100,
    )


@pytest.mark.parametrize("field", ("occurrence", "observation"))
@pytest.mark.parametrize("size", (0, 63, 65, 65_536))
def test_candidate_digest_requires_exact_width_before_history(
    field: str, size: int,
) -> None:
    arguments = {"occurrence": "c" * 64, "observation": "d" * 64}
    arguments[field] = "e" * size
    with pytest.raises(
        attention.AttentionPreviewRejected, match="exact bounded",
    ):
        _review(_policy(), **arguments)


@pytest.mark.parametrize("field", ("scope_sha256", "trigger_sha256"))
@pytest.mark.parametrize("size", (65, 65_536))
def test_policy_digest_requires_exact_width_before_hash(
    field: str, size: int,
) -> None:
    policy = replace(_policy(), **{field: "e" * size})
    with pytest.raises(
        attention.AttentionPreviewRejected, match="invalid bounded attention policy",
    ):
        _review(policy)


@pytest.mark.parametrize(
    "field", (
        "scope_sha256", "trigger_sha256",
        "occurrence_sha256", "observation_sha256",
    ),
)
def test_history_digest_requires_exact_width_before_review(field: str) -> None:
    marker = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "e" * 64, "f" * 64, 50,
    )
    bad = replace(marker, **{field: "f" * 65_536})
    with pytest.raises(
        attention.AttentionPreviewRejected, match="history incoherent",
    ):
        _review(_policy(), (bad,))


def test_valid_width_keeps_denial_only_disconnected_review() -> None:
    result = _review(_policy())
    assert result.disposition == "REVIEW_ONLY"
    assert result.notification_authorized is False
    assert result.action_authorized is False
    assert result.consent_verified is False
    assert result.trusted_clock_verified is False
