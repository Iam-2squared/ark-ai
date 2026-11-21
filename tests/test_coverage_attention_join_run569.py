"""Synthetic transcript coverage-to-attention binding must remain deny-only."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import offline_coverage_attention_join as join
from ark import offline_transcript_coverage as coverage
from ark import proactive_attention_preview as attention

SCOPE = "a" * 64
TRIGGER = "b" * 64
OBSERVATION = "c" * 64
OCCURRENCE = "e" * 64
DIGEST = "f" * 64


def fixture_coverage():
    return coverage.OfflineTranscriptCoverage(
        OBSERVATION, "1" * 64, 100, 80, 10, 5, 5,
        800_000, 3, 10, DIGEST,
    )


def fixture_policy():
    return attention.AttentionBudgetPolicy(SCOPE, TRIGGER, 100, 1000, 2, False)


def check(c=None, history=(), threshold=800_000, *, retained=None,
          occurrence=OCCURRENCE, now=200):
    c = fixture_coverage() if c is None else c
    return join.review_detached_coverage_attention(
        c, fixture_policy(), tuple(history),
        retained_coverage_sha256=DIGEST if retained is None else retained,
        occurrence_sha256=occurrence, observed_now_ms=now,
        required_coverage_ppm=threshold,
    )


@pytest.mark.parametrize("threshold,expected", (
    (0, "REVIEW_ONLY"),
    (799_999, "REVIEW_ONLY"),
    (800_000, "REVIEW_ONLY"),
    (800_001, "INSUFFICIENT_COVERAGE_HOLD"),
    (1_000_000, "INSUFFICIENT_COVERAGE_HOLD"),
))
def test_threshold_is_only_a_synthetic_hold_not_grant(threshold, expected):
    r = check(threshold=threshold)
    assert r.disposition == expected
    assert r.coverage_ppm == 800_000
    assert r.required_coverage_ppm == threshold
    assert r.sensor_authenticated is False
    assert r.consent_verified is False
    assert r.notification_authorized is False
    assert r.tool_execution_authorized is False
    assert len(r.receipt_sha256) == 64
    assert r == check(threshold=threshold)


def test_duplicate_occurrence_is_preserved_even_under_low_coverage():
    row = attention.SyntheticSurfaceMarker(
        SCOPE, TRIGGER, OCCURRENCE, OBSERVATION, 100,
    )
    r = check(history=(row,), now=200, threshold=900_000)
    assert r.disposition == "ALREADY_RECORDED"


def test_cooldown_is_preserved_under_low_coverage():
    row = attention.SyntheticSurfaceMarker(
        SCOPE, TRIGGER, "2" * 64, "3" * 64, 100,
    )
    assert check(history=(row,), now=150, threshold=900_000).disposition == (
        "COOLDOWN_HOLD"
    )


@pytest.mark.parametrize("overrides", (
    {"audio_frames": 0},
    {"audio_frames": True},
    {"covered_frames": 101},
    {"leading_gap_frames": -1},
    {"trailing_gap_frames": 99},
    {"coverage_ppm": 999999},
    {"coverage_sha256": "a" * 64},
    {"observation_sha256": "INVALID"},
))
def test_forged_or_incoherent_coverage_is_refused(overrides):
    with pytest.raises(join.DetachedCoverageAttentionRejected):
        check(replace(fixture_coverage(), **overrides))


@pytest.mark.parametrize("bad", (True, -1, 1_000_001, None))
def test_threshold_types_and_range_are_exact(bad):
    with pytest.raises(join.DetachedCoverageAttentionRejected, match="inputs"):
        check(threshold=bad)


def test_altered_caller_retained_digest_refused():
    with pytest.raises(join.DetachedCoverageAttentionRejected, match="accounting"):
        check(retained="1" * 64)


@pytest.mark.parametrize("flag", join._RESULT_DENIALS)
def test_import_pinned_deny_only_properties_cannot_be_replaced(monkeypatch, flag):
    monkeypatch.setattr(join.DetachedCoverageAttention, flag, property(lambda _: False))
    with pytest.raises(join.DetachedCoverageAttentionRejected, match="authority changed"):
        check()


@pytest.mark.parametrize("flag", join._ATTENTION_DENIAL_NAMES)
def test_underlying_attention_denial_substitutions_are_rejected(monkeypatch, flag):
    monkeypatch.setattr(attention.AttentionBudgetPreview,
                        flag, property(lambda _: False))
    with pytest.raises(join.DetachedCoverageAttentionRejected, match="authority changed"):
        check()


def test_substituted_hash_refused_before_coverage_mutation(monkeypatch):
    c = fixture_coverage()
    original = join.hashlib.sha256
    # The original dependency remains pinned. Simulate a hash callback
    # mutating a caller-supplied receipt after validation.
    calls = []

    def change(data):
        calls.append(True)
        object.__setattr__(c, "coverage_sha256", "9" * 64)
        return original(data)

    monkeypatch.setattr(join.hashlib, "sha256", change)
    with pytest.raises(
        join.DetachedCoverageAttentionRejected, match="attention preview rejected",
    ):
        check(c)
    assert calls == []
    assert c.coverage_sha256 == DIGEST
