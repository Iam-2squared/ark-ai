"""A synthetic second SQLite writer cannot be mistaken for a stable CAS result.

The two child reviewers and the repeat pass must agree when an independent
local writer advances or replaces the same Memory generation between passes.
These are read-only diagnostic calls: no claim of caller attribution or retry.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import SQLiteMemoryStore
from ark.memory import ambiguous_commit_pair_review as pair
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


@pytest.mark.parametrize(
    "phase",
    ("between_child_reviews", "between_complete_passes", "lifetime_replacement"),
)
def test_cross_handle_write_during_pair_review_never_authenticates_commit(
    tmp_path, monkeypatch, phase,
):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    other = SQLiteMemoryStore(store.path, clock_ms=lambda: 1000)
    triage_original = pair._TRIAGE_FN
    outcome_original = pair._OUTCOME_FN
    calls = 0
    injected = False

    def independent_writer():
        nonlocal injected
        assert not injected
        injected = True
        if phase == "lifetime_replacement":
            assert other.delete(saved.memory_id, scope, expected_revision=1)
            other.put(proposed, expected_revision=0)
        else:
            generation_fenced_memory_update(other, proposed, retained=retained)

    def triage_hook(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2 and phase != "between_child_reviews":
            independent_writer()
        return triage_original(*args, **kwargs)

    def outcome_hook(*args, **kwargs):
        if phase == "between_child_reviews" and not injected:
            independent_writer()
        return outcome_original(*args, **kwargs)

    # The paired reviewer requires its pinned functions and the exported
    # module hooks to agree. Fault injection changes both deliberately.
    monkeypatch.setattr(pair, "_TRIAGE_FN", triage_hook)
    monkeypatch.setattr(pair.triage_module, "review_uncertain_memory_commit", triage_hook)
    monkeypatch.setattr(pair, "_OUTCOME_FN", outcome_hook)
    monkeypatch.setattr(
        pair.outcome_module, "review_memory_generation_cas_outcome", outcome_hook,
    )

    with pytest.raises(pair.MemoryAmbiguityPairRejected):
        pair.review_memory_ambiguous_commit_pair(
            store, proposed, retained=retained,
        )
    assert injected
    # The only durable mutation was made explicitly by the second handle,
    # not an implicit retry by either read-only child reviewer.
    assert [event.operation for event in store.events(scope)] == (
        ["create", "delete", "create"]
        if phase == "lifetime_replacement" else ["create", "update"]
    )
    assert store.get(saved.memory_id, scope).content == proposed.content
