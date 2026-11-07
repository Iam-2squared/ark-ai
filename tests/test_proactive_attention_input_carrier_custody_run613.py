"""Disconnected proactive attention rejects imported input type replacement.

All markers and clocks are synthetic. This preview never sends notifications
and never proves consent, trusted time, or real-world delivery.
"""

import pytest

from ark import proactive_attention_preview as attention

SCOPE = "a" * 64
TRIGGER = "b" * 64
FIRST = "c" * 64
CURRENT = "d" * 64
PREVIOUS_OBSERVATION = "e" * 64
CURRENT_OBSERVATION = "f" * 64


def _policy(*, cooldown=1, limit=1, suppress=False):
    return attention.AttentionBudgetPolicy(
        SCOPE, TRIGGER, cooldown, 100, limit, suppress,
    )


def _marker(at, *, occurrence=FIRST, observation=PREVIOUS_OBSERVATION):
    return attention.SyntheticSurfaceMarker(
        SCOPE, TRIGGER, occurrence, observation, at,
    )


def _preview(policy, history, *, now=500, occurrence=CURRENT, observation=CURRENT_OBSERVATION):
    return attention.preview_proactive_attention(
        policy, history, occurrence_sha256=occurrence,
        observation_sha256=observation, observed_now_ms=now,
    )


@pytest.mark.parametrize("target", ("AttentionBudgetPolicy", "SyntheticSurfaceMarker"))
def test_counterfeit_input_class_refused_before_any_field_getter(monkeypatch, target):
    calls = []

    class Counterfeit:
        def __getattribute__(self, key):
            calls.append(key)
            raise AssertionError("untrusted carrier getter invoked")

    policy = _policy()
    history = (_marker(400),)
    monkeypatch.setattr(attention, target, Counterfeit)
    if target == "AttentionBudgetPolicy":
        policy = Counterfeit()
    else:
        history = (Counterfeit(),)
    with pytest.raises(attention.AttentionPreviewRejected, match="authority definition"):
        _preview(policy, history)
    assert calls == []


@pytest.mark.parametrize(
    ("last_at", "limit", "cooldown", "expected", "next_at", "active"),
    (
        (400, 1, 1, "REVIEW_ONLY", None, 0),
        (401, 1, 1, "WINDOW_BUDGET_HOLD", 501, 1),
        (450, 2, 50, "REVIEW_ONLY", None, 1),
        (451, 2, 50, "COOLDOWN_HOLD", 501, 1),
    ),
)
def test_window_and_cooldown_edges_are_deterministic(
    last_at, limit, cooldown, expected, next_at, active,
):
    report = _preview(
        _policy(cooldown=cooldown, limit=limit), (_marker(last_at),),
    )
    assert report.disposition == expected
    assert report.next_review_at_ms == next_at
    assert report.surfaced_count_in_window == active
    assert report.notification_authorized is False
    assert report.action_authorized is False


@pytest.mark.parametrize(
    ("occurrence", "observation", "expected"),
    (
        (FIRST, CURRENT_OBSERVATION, "ALREADY_RECORDED"),
        (CURRENT, PREVIOUS_OBSERVATION, "UNCHANGED_SUPPRESSED"),
    ),
)
def test_duplicate_occurrence_or_unchanged_observation_is_never_review_ready(
    occurrence, observation, expected,
):
    report = _preview(
        _policy(cooldown=10, limit=2, suppress=True),
        (_marker(450),), occurrence=occurrence, observation=observation,
    )
    assert report.disposition == expected
    assert report.notification_authorized is False
    assert report.consent_verified is False


@pytest.mark.parametrize("history", (
    (_marker(501),),
    (_marker(400), _marker(450, occurrence=FIRST)),
))
def test_incoherent_or_duplicate_history_rejected(history):
    with pytest.raises(attention.AttentionPreviewRejected, match="history incoherent"):
        _preview(_policy(), history)


def test_next_review_timestamp_cannot_overflow_sqlite_64bit():
    maximum = 2**63 - 1
    with pytest.raises(
        attention.AttentionPreviewRejected, match="unrepresentable",
    ):
        _preview(
            _policy(cooldown=1), (_marker(maximum),), now=maximum,
        )


def test_empty_synthetic_history_remains_review_only_without_permission():
    report = _preview(_policy(), ())
    assert report.disposition == "REVIEW_ONLY"
    assert report.next_review_at_ms is None
    assert report.notification_authorized is False
    assert report.action_authorized is False
    assert report.trusted_clock_verified is False
    assert report.consent_verified is False
