"""Manual-only CAS outcome decisions cannot rely on replaceable equality.

All changes are local SQLite test fixtures; no automatic retry, consent,
author attribution, trusted time, or external ToolBackend execution.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as outcome
from ark.memory import generation_fenced_cas as cas


def _case(tmp_path):
    path = tmp_path / "outcome-epoch.sqlite"
    scope = MemoryScope("outcome-fixture", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    store.put(
        MemoryWrite(scope, "stable", "original", expires_at_ms=3000),
        expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(
        scope, "stable", "new", {"source": "synthetic"}, expires_at_ms=2900,
    )
    return path, scope, store, retained, proposed


@pytest.mark.parametrize("new_value", ("matching", "different"))
def test_replaced_token_equality_and_preinstalled_denial_block_writer(
    tmp_path, monkeypatch, new_value,
):
    path, scope, store, retained, proposed = _case(tmp_path)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1100)
    calls = []

    def write_and_deny(self):
        if not calls:
            calls.append(new_value)
            value = "new" if new_value == "matching" else "other"
            writer.put(
                MemoryWrite(
                    scope, "stable", value, {"source": "synthetic"},
                    expires_at_ms=2900,
                ),
                expected_revision=1,
            )
        return False

    monkeypatch.setattr(
        cas.MemoryGenerationCASToken, "__eq__", lambda self, other: True,
    )
    monkeypatch.setattr(
        outcome.MemoryCASOutcomeReview, "automatic_retry_authorized",
        property(write_and_deny),
    )
    with pytest.raises(outcome.MemoryCASOutcomeRejected, match="authority definition changed"):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert calls == []  # Preinstalled malicious getter quarantined before DB read.
    assert len(writer.events(scope)) == 1


@pytest.mark.parametrize("field", ("review_sha256", "observed_row_sha256"))
def test_preinstalled_equal_text_mutation_callback_is_rejected(
    tmp_path, monkeypatch, field,
):
    _, _, store, retained, proposed = _case(tmp_path)

    def replace_equal(self):
        original = getattr(self, field)
        clone = ("#" + original)[1:]
        assert clone == original and clone is not original
        object.__setattr__(self, field, clone)
        return False

    monkeypatch.setattr(
        outcome.MemoryCASOutcomeReview, "external_action_authorized",
        property(replace_equal),
    )
    with pytest.raises(outcome.MemoryCASOutcomeRejected, match="authority definition changed"):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )


def test_preinstalled_getter_cannot_reach_observed_token(
    tmp_path, monkeypatch,
):
    _, _, store, retained, proposed = _case(tmp_path)
    native = outcome._snapshot
    tokens = []

    def capture(*args):
        row, token = native(*args)
        tokens.append(token)
        return row, token

    def mutate_observation(self):
        token = tokens[0]
        old = token.row_sha256
        clone = ("#" + old)[1:]
        assert clone == old and clone is not old
        object.__setattr__(token, "row_sha256", clone)
        return False

    monkeypatch.setattr(outcome, "_snapshot", capture)
    monkeypatch.setattr(
        outcome.MemoryCASOutcomeReview, "external_action_authorized",
        property(mutate_observation),
    )
    with pytest.raises(outcome.MemoryCASOutcomeRejected, match="authority definition changed"):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert tokens == []


def test_unmodified_outcome_remains_non_authorizing(tmp_path):
    _, _, store, retained, proposed = _case(tmp_path)
    report = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert report.observation == "UNCHANGED_OBSERVED"
    assert report.automatic_retry_authorized is False
    assert report.commit_attributed_to_caller is False
