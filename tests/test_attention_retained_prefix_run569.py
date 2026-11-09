"""Detached attention restart evidence: no notifications or automatic replay."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import attention_retained_prefix_review as prefix
from ark import proactive_attention_preview as attention

_MISSING = object()
SCOPE = "a" * 64
TRIGGER = "b" * 64


def policy():
    return attention.AttentionBudgetPolicy(SCOPE, TRIGGER, 100, 1000, 3, False)


def marker(number, at):
    return attention.SyntheticSurfaceMarker(
        SCOPE, TRIGGER, f"{number:064x}", f"{number + 50:064x}", at,
    )


def digest(p, rows, now):
    return attention.preview_proactive_attention(
        p, rows, occurrence_sha256="0" * 64,
        observation_sha256="0" * 64, observed_now_ms=now,
    ).history_sha256


def check(old=(), new=(), old_now=100, now=200, *, p=None, old_digest=_MISSING):
    p = policy() if p is None else p
    return prefix.review_attention_retained_prefix(
        p, tuple(old), tuple(new),
        retained_history_sha256=(
            digest(p, tuple(old), old_now) if old_digest is _MISSING else old_digest
        ),
        retained_now_ms=old_now, observed_now_ms=now,
    )


@pytest.mark.parametrize("old,new,old_now,now,classification,added", (
    ((), (), 100, 100, "UNCHANGED", 0),
    ((), (marker(1, 101),), 100, 200, "APPEND_ONLY", 1),
    ((marker(1, 100),), (marker(1, 100),), 100, 200, "UNCHANGED", 0),
    ((marker(1, 100),), (marker(1, 100), marker(2, 150)),
     100, 200, "APPEND_ONLY", 1),
))
def test_empty_same_or_appended_history_is_review_only(
    old, new, old_now, now, classification, added,
):
    result = check(old, new, old_now, now)
    assert result.classification == classification
    assert result.retained_count == len(old)
    assert result.observed_count == len(new)
    assert result.appended_count == added
    assert len(result.evidence_sha256) == 64
    assert result.append_authorized is False
    assert result.notification_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.clock_authenticated is False
    assert result == check(old, new, old_now, now)


@pytest.mark.parametrize("old,new", (
    ((marker(1, 100),), ()),
    ((marker(1, 100),), (marker(2, 100),)),
    ((marker(1, 100), marker(2, 150)), (marker(2, 150), marker(1, 100))),
    ((marker(1, 100),), (marker(1, 101),)),
))
def test_deleted_rewritten_or_reordered_prefix_never_passes(old, new):
    with pytest.raises(prefix.AttentionPrefixRejected):
        check(old, new, 150, 200)


@pytest.mark.parametrize("bad", (
    "A" * 64, "x" * 64, "0" * 63, "", None,
))
def test_retained_digest_must_match_recomputed_history(bad):
    with pytest.raises(prefix.AttentionPrefixRejected):
        check((marker(1, 100),), (marker(1, 100),),
              100, 200, old_digest=bad)


@pytest.mark.parametrize("old_now,now", ((101, 100), (-1, 200),
                                          (100, 2**63), (True, 200)))
def test_untrusted_clock_and_nonexact_carriers_rejected(old_now, now):
    with pytest.raises(prefix.AttentionPrefixRejected):
        check((), (), old_now, now, old_digest="0" * 64)


def test_future_or_duplicate_appended_occurrence_rejected():
    with pytest.raises(prefix.AttentionPrefixRejected, match="source preview rejected"):
        check((), (marker(1, 201),), 100, 200)
    with pytest.raises(prefix.AttentionPrefixRejected, match="source preview rejected"):
        check((), (marker(1, 100), marker(1, 150)), 100, 200)


def test_equal_value_copied_immutable_prior_markers_allowed():
    old = (marker(1, 100),)
    new = (replace(old[0]), marker(2, 150))
    assert check(old, new, 100, 200).classification == "APPEND_ONLY"


@pytest.mark.parametrize("flag", prefix._OUTPUT_DENIALS)
def test_import_pinned_false_only_authority_cannot_be_replaced(
    monkeypatch, flag,
):
    monkeypatch.setattr(prefix.AttentionPrefixReview, flag, property(lambda _: False))
    with pytest.raises(prefix.AttentionPrefixRejected, match="authority changed"):
        check()


def test_preview_dependency_is_pinned_before_processing(monkeypatch):
    original = attention.preview_proactive_attention
    monkeypatch.setattr(attention, "preview_proactive_attention", lambda *a, **kw: None)
    with pytest.raises(prefix.AttentionPrefixRejected, match="authority changed"):
        prefix.review_attention_retained_prefix(
            policy(), (), (), retained_history_sha256="0" * 64,
            retained_now_ms=100, observed_now_ms=200,
        )
    assert original is prefix._PREVIEW


def test_substituted_hash_refused_before_history_mutation(monkeypatch):
    old = (marker(1, 100),)
    new = (marker(1, 100), marker(2, 150))
    old_digest = digest(policy(), old, 100)
    real = prefix.hashlib.sha256
    calls = [0]

    def mutate(data):
        calls[0] += 1
        if calls[0] == 1:
            object.__setattr__(new[1], "observation_sha256", "e" * 64)
        return real(data)

    monkeypatch.setattr(prefix.hashlib, "sha256", mutate)
    with pytest.raises(
        prefix.AttentionPrefixRejected, match="attention source preview rejected",
    ):
        check(old, new, 100, 200, old_digest=old_digest)
    assert calls == [0]
    assert new[1].observation_sha256 == f"{52:064x}"
