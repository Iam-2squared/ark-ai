"""Two independent Memory diagnostics remain passive after an ambiguous write.

All writes below are explicit local synthetic fixtures from a *different*
SQLite handle. Even identical persisted bytes cannot attribute a COMMIT to the
caller or authorize an automatic retry, disclosure or real-world action.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import (
    observe_memory_generation_for_cas,
)
from ark.memory.postcommit_uncertainty_review import (
    review_uncertain_memory_commit,
)


@pytest.mark.parametrize(
    ("external_write", "expected_triage", "expected_outcome"),
    (
        ("unrelated", "LOCAL_UNCHANGED", "UNCHANGED_OBSERVED"),
        (
            "matching",
            "ONE_MATCHING_UPDATE_VISIBLE",
            "ONE_MATCHING_UPDATE_OBSERVED",
        ),
        ("different_metadata", "INDETERMINATE", "DIVERGED_OBSERVED"),
        ("double_matching", "INDETERMINATE", "DIVERGED_OBSERVED"),
    ),
)
def test_dual_commit_unknown_reviews_never_attribute_independent_writer(
    tmp_path, external_write, expected_triage, expected_outcome,
):
    path = tmp_path / "two-diagnostic-ambiguous.sqlite"
    scope = MemoryScope("private-owner", "offline")
    reviewer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    other = SQLiteMemoryStore(path, clock_ms=lambda: 1100)
    original = reviewer.put(MemoryWrite(scope, "target", "before"))
    retained = observe_memory_generation_for_cas(reviewer, scope, "target")
    proposed = MemoryWrite(
        scope, "target", "after", metadata={"privacy": "local"},
        expires_at_ms=5000,
    )

    # The unrelated event can occur before a target write; the global SQLite
    # event number is not a caller identity or a target-row generation token.
    other.put(
        MemoryWrite(MemoryScope("another-owner", "offline"), "side", "side"),
    )
    if external_write == "matching":
        other.put(proposed, expected_revision=1)
    elif external_write == "different_metadata":
        other.put(
            MemoryWrite(
                scope, "target", "after", metadata={"privacy": "different"},
                expires_at_ms=5000,
            ),
            expected_revision=1,
        )
    elif external_write == "double_matching":
        other.put(proposed, expected_revision=1)
        other.put(proposed, expected_revision=2)

    before_events = reviewer.events(scope)
    before_record = reviewer.get(original.memory_id, scope, include_expired=True)
    triage = review_uncertain_memory_commit(
        reviewer, proposed, retained_before=retained,
    )
    outcome = review_memory_generation_cas_outcome(
        reviewer, proposed, retained=retained,
    )

    assert triage.disposition == expected_triage
    assert outcome.observation == expected_outcome
    assert triage.retained_prefix_sha256 == outcome.retained_prefix_sha256
    assert triage.observed_prefix_sha256 == outcome.observed_prefix_sha256
    assert triage.automatic_retry_authorized is False
    assert triage.write_authorized is False
    assert triage.caller_attribution_proven is False
    assert triage.trusted_clock_proven is False
    assert outcome.commit_attributed_to_caller is False
    assert outcome.automatic_retry_authorized is False
    assert outcome.consent_authenticated is False
    assert outcome.external_action_authorized is False
    assert outcome.trusted_clock_verified is False
    assert reviewer.events(scope) == before_events
    assert reviewer.get(
        original.memory_id, scope, include_expired=True,
    ) == before_record
