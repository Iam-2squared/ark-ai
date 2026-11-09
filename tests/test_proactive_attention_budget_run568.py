"""Offline attention-window decisions remain bounded and deny-only."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import proactive_attention_preview as attention

SCOPE = "a" * 64
TRIGGER = "b" * 64
CURRENT = "e" * 64


def _policy(**overrides):
    return replace(
        attention.AttentionBudgetPolicy(
            SCOPE, TRIGGER, 100, 1000, 2, True,
        ),
        **overrides,
    )


def _marker(n, at, *, observation=None, scope=SCOPE, trigger=TRIGGER):
    return attention.SyntheticSurfaceMarker(
        scope, trigger, f"{n:064x}", observation or f"{n + 20:064x}", at,
    )


def _review(history=(), *, now=0, policy=None, occurrence=CURRENT,
            observation=CURRENT):
    return attention.preview_proactive_attention(
        _policy() if policy is None else policy, tuple(history),
        occurrence_sha256=occurrence, observation_sha256=observation,
        observed_now_ms=now,
    )


def test_empty_history_is_only_review_eligible_never_a_notification_grant():
    report = _review(now=100)
    assert report.disposition == "REVIEW_ONLY"
    assert report.surfaced_count_in_window == 0
    assert report.next_review_at_ms is None
    assert len(report.history_sha256) == len(report.review_sha256) == 64
    assert report.notification_authorized is False
    assert report.action_authorized is False
    assert report.trusted_clock_verified is False
    assert report.consent_verified is False
    assert report == _review(now=100)


@pytest.mark.parametrize(
    ("now", "disposition", "next_at"),
    (
        (100, "COOLDOWN_HOLD", 200),
        (199, "COOLDOWN_HOLD", 200),
        (200, "REVIEW_ONLY", None),
    ),
)
def test_cooldown_is_inclusive_at_exact_boundary(now, disposition, next_at):
    report = _review((_marker(1, 100),), now=now)
    assert report.disposition == disposition
    assert report.next_review_at_ms == next_at


@pytest.mark.parametrize(
    ("now", "expected", "count"),
    (
        (999, "WINDOW_BUDGET_HOLD", 2),
        (1099, "WINDOW_BUDGET_HOLD", 2),
        (1100, "REVIEW_ONLY", 1),
    ),
)
def test_window_start_exclusive_and_release_exact(now, expected, count):
    report = _review(
        (_marker(1, 100), _marker(2, 200)),
        now=now, policy=_policy(cooldown_ms=10),
    )
    assert report.disposition == expected
    assert report.surfaced_count_in_window == count
    assert report.next_review_at_ms == (1100 if count == 2 else None)


def test_duplicate_occurrence_precedes_cooldown_and_unmodified_observation():
    marker = _marker(1, 100)
    assert _review(
        (marker,), now=100, occurrence=marker.occurrence_sha256,
        observation=marker.observation_sha256,
    ).disposition == "ALREADY_RECORDED"


@pytest.mark.parametrize("suppress", (True, False))
def test_unchanged_observation_suppression_is_explicit(suppress):
    marker = _marker(1, 100)
    report = _review(
        (marker,), now=2000, observation=marker.observation_sha256,
        policy=_policy(suppress_unchanged=suppress),
    )
    assert report.disposition == (
        "UNCHANGED_SUPPRESSED" if suppress else "REVIEW_ONLY"
    )


@pytest.mark.parametrize(
    "history,now",
    (
        ((_marker(1, 100, scope="d" * 64),), 200),
        ((_marker(1, 100, trigger="d" * 64),), 200),
        ((_marker(1, 100), _marker(2, 100)), 200),
        ((_marker(1, 100), _marker(2, 99)), 200),
        ((_marker(1, 100), _marker(1, 200)), 200),
        ((_marker(1, 101),), 100),
    ),
)
def test_cross_scope_reordered_duplicate_or_future_evidence_fails(history, now):
    with pytest.raises(attention.AttentionPreviewRejected, match="incoherent"):
        _review(history, now=now)


@pytest.mark.parametrize(
    "overrides",
    (
        {"scope_sha256": "INVALID"},
        {"trigger_sha256": "A" * 64},
        {"cooldown_ms": True},
        {"cooldown_ms": 0},
        {"rolling_window_ms": 0},
        {"max_surfaced_per_window": 0},
        {"max_surfaced_per_window": 257},
        {"suppress_unchanged": 1},
    ),
)
def test_invalid_policy_fails_closed(overrides):
    with pytest.raises(attention.AttentionPreviewRejected, match="policy"):
        _review(policy=_policy(**overrides))


@pytest.mark.parametrize("name", attention._DENIAL_NAMES)
def test_preinstalled_false_authority_getter_refused_before_hash(
    monkeypatch, name,
):
    def forbidden(*args, **kwargs):
        pytest.fail("preinstalled authority substitution reached hashing")

    monkeypatch.setattr(
        attention.AttentionBudgetPreview, name, property(lambda _: False),
    )
    monkeypatch.setattr(attention.hashlib, "sha256", forbidden)
    with pytest.raises(
        attention.AttentionPreviewRejected, match="authority definition changed",
    ):
        _review(now=100)


def test_substituted_hash_callback_cannot_retarget_history_before_validation(monkeypatch):
    marker = _marker(1, 100)
    original = attention.hashlib.sha256

    calls = []

    def mutate(data):
        calls.append(True)
        object.__setattr__(marker, "observation_sha256", "d" * 64)
        return original(data)

    monkeypatch.setattr(attention.hashlib, "sha256", mutate)
    with pytest.raises(
        attention.AttentionPreviewRejected, match="authority definition changed",
    ):
        _review((marker,), now=200)
    assert calls == []
    assert marker.observation_sha256 == f"{21:064x}"


def test_final_false_getter_cannot_retarget_result_sha(monkeypatch):
    original = attention.AttentionBudgetPreview.__getattribute__

    def mutate(self, name):
        if name == "consent_verified":
            object.__setattr__(self, "review_sha256", "0" * 64)
            return False
        return original(self, name)

    monkeypatch.setattr(
        attention.AttentionBudgetPreview, "__getattribute__", mutate,
    )
    with pytest.raises(attention.AttentionPreviewRejected, match="result changed"):
        _review(now=200)


def test_digest_binds_policy_history_candidate_and_clock_without_plaintext():
    marker = _marker(1, 100)
    first = _review((marker,), now=200)
    second = _review((marker,), now=201)
    changed = _review((marker,), now=200, policy=_policy(cooldown_ms=50))
    assert first.history_sha256 == second.history_sha256
    assert first.review_sha256 != second.review_sha256
    assert changed.history_sha256 != first.history_sha256
    assert SCOPE not in repr(first)
