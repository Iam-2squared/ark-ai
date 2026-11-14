"""Dual independent read-only Memory COMMIT ambiguity reconciliation."""

from __future__ import annotations

from dataclasses import replace

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark import memory
from ark.memory import ambiguous_commit_pair_review as mod
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


def _review(store, proposed, retained):
    return mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )


def test_unchanged_prefix_is_manual_only_and_deterministic(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    first = _review(store, proposed, retained)
    assert first == _review(store, proposed, retained)
    assert first.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert first.retained_prefix_sha256 == first.observed_prefix_sha256
    assert len(first.reconciliation_sha256) == 64
    assert all(getattr(first, name) is False for name in mod._DENIALS)


def test_one_matching_update_is_visible_not_attributed(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    generation_fenced_memory_update(store, proposed, retained=retained)
    review = _review(store, proposed, retained)
    assert review.disposition == "MATCHING_ROW_MANUAL_REVIEW"
    assert review.retained_prefix_sha256 != review.observed_prefix_sha256
    assert review.automatic_retry_authorized is False
    assert review.caller_commit_authenticated is False


def test_different_local_row_requires_manual_divergence(tmp_path):
    store, scope, _, retained, proposed = make_case(tmp_path)
    other = memory.MemoryWrite(scope, "stable", "other", metadata={"source": "local"})
    generation_fenced_memory_update(store, other, retained=retained)
    review = _review(store, proposed, retained)
    assert review.disposition == "DIVERGED_MANUAL_REVIEW"
    assert review.write_authorized is False


def test_invalid_retained_history_never_authorizes_retry(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    forged = replace(retained, event_prefix_sha256="f" * 64)
    with pytest.raises(mod.MemoryAmbiguityPairRejected):
        _review(store, proposed, forged)


@pytest.mark.parametrize("name", mod._DENIALS)
def test_preinstalled_false_only_pair_authority_swap_denied_before_database(
    monkeypatch, tmp_path, name,
):
    store, _, _, retained, proposed = make_case(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("spoofed authority should reject before any SQLite review")

    monkeypatch.setattr(type(store), "_connect_readonly", forbidden)
    monkeypatch.setattr(mod.MemoryAmbiguityPair, name, property(lambda _: False))
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="authority changed"):
        _review(store, proposed, retained)


def test_callback_can_not_mutate_original_proposed_payload(
    monkeypatch, tmp_path,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    original = mod._TRIAGE_FN

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(proposed, "content", "not my proposed content")
        return result

    monkeypatch.setattr(mod, "_TRIAGE_FN", mutate)
    monkeypatch.setattr(mod.triage_module, "review_uncertain_memory_commit", mutate)
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="epoch changed"):
        _review(store, proposed, retained)


def test_dual_review_disagreement_rejected_without_retry(monkeypatch, tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    original = mod._OUTCOME_FN

    def inconsistent(*args, **kwargs):
        result = original(*args, **kwargs)
        return replace(result, observation="DIVERGED_OBSERVED")

    monkeypatch.setattr(mod, "_OUTCOME_FN", inconsistent)
    monkeypatch.setattr(
        mod.outcome_module, "review_memory_generation_cas_outcome", inconsistent,
    )
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="child digest mismatch"):
        _review(store, proposed, retained)


def test_second_read_drift_rejected_without_attribution(monkeypatch, tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    native = mod._OUTCOME_FN
    calls = 0

    def changed_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = native(*args, **kwargs)
        if calls == 2:
            return replace(result, observed_row_sha256="f" * 64)
        return result

    monkeypatch.setattr(mod, "_OUTCOME_FN", changed_second)
    monkeypatch.setattr(
        mod.outcome_module, "review_memory_generation_cas_outcome", changed_second,
    )
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="child digest mismatch"):
        _review(store, proposed, retained)
    assert calls == 2
