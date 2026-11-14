"""CAS ambiguity review must reconcile the returned row with its token.

All fault injections operate on detached Python objects in disposable local
SQLite fixtures. The reviewer never retries a write or attributes a commit.
"""

from __future__ import annotations

import hashlib

import pytest
from test_memory_generation_cas_outcome_run536 import _case

from ark.memory import MemoryWrite
from ark.memory import generation_cas_outcome_review as outcome


@pytest.mark.parametrize(
    "field",
    ("content", "content_sha256", "metadata", "expires_at_ms", "scope"),
)
def test_second_snapshot_cannot_rewrite_first_observed_row(
    tmp_path, monkeypatch, field,
):
    store, scope, first, retained, proposed = _case(tmp_path)
    original = outcome._snapshot
    seen = []

    def intercept(*args):
        result = original(*args)
        seen.append(result)
        if len(seen) == 2:
            row = seen[0][0]
            if field == "scope":
                object.__setattr__(row.scope, "namespace", "forged")
            else:
                replacements = {
                    "content": "forged",
                    "content_sha256": hashlib.sha256(b"forged").hexdigest(),
                    "metadata": {"test": "forged"},
                    "expires_at_ms": 1800,
                }
                object.__setattr__(row, field, replacements[field])
        return result

    monkeypatch.setattr(outcome, "_snapshot", intercept)
    with pytest.raises(outcome.MemoryCASOutcomeRejected):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert len(seen) >= 2
    # Detached Python witness mutation must never modify SQLite or replay.
    assert store.get(first.memory_id, scope, include_expired=True).content == "first"
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_forged_matching_row_cannot_relabel_divergent_update(
    tmp_path, monkeypatch,
):
    store, scope, first, retained, proposed = _case(tmp_path)
    store.put(
        MemoryWrite(
            scope, "stable", "other", dict(proposed.metadata),
            expires_at_ms=proposed.expires_at_ms,
        ),
        expected_revision=1,
    )
    genuine = outcome._snapshot
    seen = []

    def intercept(*args):
        answer = genuine(*args)
        seen.append(answer)
        if len(seen) == 2:
            first_row = seen[0][0]
            object.__setattr__(first_row, "content", proposed.content)
            object.__setattr__(
                first_row, "content_sha256",
                hashlib.sha256(proposed.content.encode("utf-8")).hexdigest(),
            )
        return answer

    monkeypatch.setattr(outcome, "_snapshot", intercept)
    with pytest.raises(outcome.MemoryCASOutcomeRejected):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert store.get(first.memory_id, scope, include_expired=True).content == "other"


def test_reentrant_row_hash_cannot_mutate_its_source_after_hash(
    tmp_path, monkeypatch,
):
    store, scope, first, retained, proposed = _case(tmp_path)
    original = outcome._row_hash
    calls = []

    def mutating_digest(record):
        result = original(record)
        calls.append(True)
        object.__setattr__(record, "content", "forged after digest")
        return result

    monkeypatch.setattr(outcome, "_row_hash", mutating_digest)
    with pytest.raises(outcome.MemoryCASOutcomeRejected):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert calls
    assert store.get(first.memory_id, scope, include_expired=True).content == "first"
