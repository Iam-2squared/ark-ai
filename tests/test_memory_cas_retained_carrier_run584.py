"""Generation-CAS ambiguity review retains its exact original witness fields.

Local SQLite and fault-injected read-only callbacks only. Neither a matching
result nor an altered witness grants consent, automatic retry or provenance.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as review
from ark.memory import generation_fenced_cas as cas


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    row = store.put(
        MemoryWrite(scope, "stable", "first", expires_at_ms=2000),
        expected_revision=0,
    )
    token = cas.observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(
        scope, "stable", "proposed", {"kind": "synthetic"}, expires_at_ms=1900,
    )
    return store, scope, row, token, proposed


def _fresh_equal(value):
    replacement = ("!" + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize("field", (
    "memory_id", "event_prefix_sha256", "row_sha256",
))
@pytest.mark.parametrize("snapshot_call", (1, 2, 3, 4))
def test_read_callback_cannot_substitute_equal_retained_token_field(
    tmp_path, monkeypatch, field, snapshot_call,
):
    store, scope, row, token, proposed = _case(tmp_path)
    before_events = store.events(scope)
    before_row = store.get(row.memory_id, scope, include_expired=True)
    original = review._snapshot
    calls = 0

    def mutate_after_snapshot(*args, **kwargs):
        nonlocal calls
        current = original(*args, **kwargs)
        calls += 1
        if calls == snapshot_call:
            object.__setattr__(
                token, field, _fresh_equal(getattr(token, field)),
            )
        return current

    monkeypatch.setattr(review, "_snapshot", mutate_after_snapshot)
    with pytest.raises(
        review.MemoryCASOutcomeRejected,
        match="CAS generation unavailable|CAS observation inputs changed",
    ):
        review.review_memory_generation_cas_outcome(
            store, proposed, retained=token,
        )
    assert calls == snapshot_call
    assert store.events(scope) == before_events
    assert store.get(row.memory_id, scope, include_expired=True) == before_row


def test_unmodified_retained_witness_remains_denial_only(tmp_path):
    store, _, _, token, proposed = _case(tmp_path)
    result = review.review_memory_generation_cas_outcome(
        store, proposed, retained=token,
    )
    assert result.observation == "UNCHANGED_OBSERVED"
    assert result.commit_attributed_to_caller is False
    assert result.automatic_retry_authorized is False
    assert result.external_action_authorized is False
