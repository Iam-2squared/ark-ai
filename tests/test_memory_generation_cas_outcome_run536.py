"""Manual-only read-only review of a potentially ambiguous Memory CAS commit."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as review
from ark.memory import generation_fenced_cas as cas
from ark.memory.contracts import MemorySchemaError


def _case(tmp_path):
    clock = [1000]
    store = SQLiteMemoryStore(tmp_path / "cas.sqlite", clock_ms=lambda: clock[0])
    scope = MemoryScope("fixture-owner", "private")
    first = store.put(
        MemoryWrite(scope, "stable", "first", expires_at_ms=2000),
        expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(
        scope, "stable", "next", {"test": "safe"}, expires_at_ms=1900,
    )
    return store, scope, first, retained, proposed


def _assert_denied(result):
    assert result.commit_attributed_to_caller is False
    assert result.automatic_retry_authorized is False
    assert result.consent_authenticated is False
    assert result.trusted_clock_verified is False
    assert result.external_action_authorized is False
    assert len(result.review_sha256) == 64


def test_before_update_is_not_permission_to_retry(tmp_path):
    store, scope, first, retained, proposed = _case(tmp_path)
    events_before = store.events(scope)
    row_before = store.get(first.memory_id, scope, include_expired=True)
    outcome = review.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert outcome.observation == "UNCHANGED_OBSERVED"
    assert outcome.retained_prefix_sha256 == outcome.observed_prefix_sha256
    assert store.events(scope) == events_before
    assert store.get(first.memory_id, scope, include_expired=True) == row_before
    _assert_denied(outcome)


def test_matching_update_is_not_attributable_to_caller(tmp_path):
    store, scope, first, retained, proposed = _case(tmp_path)
    changed = cas.generation_fenced_memory_update(
        store, proposed, retained=retained,
    )
    assert changed.revision == 2
    outcome = review.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert outcome.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    assert outcome.expected_content_sha256 == hashlib.sha256(b"next").hexdigest()
    assert outcome.retained_prefix_sha256 != outcome.observed_prefix_sha256
    assert store.get(first.memory_id, scope, include_expired=True).revision == 2
    _assert_denied(outcome)


def test_identical_concurrent_writer_cannot_be_attributed(tmp_path):
    store, scope, _, retained, proposed = _case(tmp_path)
    # This simulated other writer, not the reviewer, advances the row.
    store.put(proposed, expected_revision=1)
    outcome = review.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert outcome.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    assert outcome.commit_attributed_to_caller is False


@pytest.mark.parametrize("difference", ("content", "metadata", "expiry"))
def test_valid_but_different_update_remains_diverged(tmp_path, difference):
    store, scope, _, retained, proposed = _case(tmp_path)
    changes = {
        "content": MemoryWrite(scope, "stable", "other", {"test": "safe"}, 1900),
        "metadata": MemoryWrite(scope, "stable", "next", {"test": "other"}, 1900),
        "expiry": MemoryWrite(scope, "stable", "next", {"test": "safe"}, 1800),
    }
    cas.generation_fenced_memory_update(
        store, changes[difference], retained=retained,
    )
    result = review.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert result.observation == "DIVERGED_OBSERVED"
    _assert_denied(result)


def test_multiple_updates_are_not_a_single_matching_commit(tmp_path):
    store, scope, _, retained, proposed = _case(tmp_path)
    first = cas.generation_fenced_memory_update(
        store, proposed, retained=retained,
    )
    assert first.revision == 2
    store.put(proposed, expected_revision=2)
    outcome = review.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert outcome.observation == "DIVERGED_OBSERVED"


@pytest.mark.parametrize("recreate", (False, True))
def test_deleted_or_recreated_generation_is_manual_only(tmp_path, recreate):
    store, scope, first, retained, proposed = _case(tmp_path)
    assert store.delete(first.memory_id, scope, expected_revision=1)
    if recreate:
        store.put(
            MemoryWrite(scope, "stable", "different", expires_at_ms=1900),
            expected_revision=0,
        )
    with pytest.raises(review.MemoryCASOutcomeRejected):
        review.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )


def test_wrong_target_is_rejected_without_writes(tmp_path):
    store, scope, _, retained, proposed = _case(tmp_path)
    events = store.events(scope)
    with pytest.raises(review.MemoryCASOutcomeRejected):
        review.review_memory_generation_cas_outcome(
            store, MemoryWrite(scope, "other", "new"), retained=retained,
        )
    assert store.events(scope) == events


@pytest.mark.parametrize("field,value", (("revision", True), ("row_sha256", "0" * 64)))
def test_mutated_or_stale_token_cannot_grant_replay(tmp_path, field, value):
    store, _, _, retained, proposed = _case(tmp_path)
    object.__setattr__(retained, field, value)
    if field == "revision":
        with pytest.raises(MemorySchemaError):
            review.review_memory_generation_cas_outcome(
                store, proposed, retained=retained,
            )
    else:
        with pytest.raises(MemorySchemaError):
            review.review_memory_generation_cas_outcome(
                store, proposed, retained=retained,
            )


def test_report_is_immutable_and_non_authorizing(tmp_path):
    store, _, _, retained, proposed = _case(tmp_path)
    result = review.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    with pytest.raises(FrozenInstanceError):
        result.observation = "APPLIED"
    _assert_denied(result)
