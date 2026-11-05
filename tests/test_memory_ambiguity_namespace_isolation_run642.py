"""COMMIT-UNKNOWN diagnostics must not conflate unrelated Memory scopes.

Synthetic local-only writers share one disposable SQLite database. A changed
other owner's or namespace's row is not evidence that our caller committed its
own update. All reconciliation remains manual and read-only.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    review_memory_ambiguous_commit_pair,
)
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


@pytest.mark.parametrize("isolation", ("other_owner", "other_namespace"))
@pytest.mark.parametrize("target_updated", (False, True))
def test_independent_scope_history_never_attributed_to_cas_caller(
    tmp_path, isolation, target_updated,
):
    store, scope, original, retained, proposed = make_case(tmp_path)
    assert type(store) is SQLiteMemoryStore
    if isolation == "other_owner":
        other_scope = MemoryScope("other-private-owner", scope.namespace)
    else:
        other_scope = MemoryScope(scope.owner_id, "other-private-namespace")

    other_source = "independent"
    other = store.put(MemoryWrite(other_scope, other_source, "version-1"))
    for revision in (1, 2):
        other = store.put(
            MemoryWrite(other_scope, other_source, f"version-{revision + 1}"),
            expected_revision=revision,
        )
    assert other.revision == 3
    original_events = store.events(scope)
    other_events = store.events(other_scope)

    if target_updated:
        # This is a separate synthetic writer, not evidence of the caller's
        # unknown outcome. A matching payload must not imply attribution.
        generation_fenced_memory_update(store, proposed, retained=retained)
    review = review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    if target_updated:
        assert review.disposition == "MATCHING_ROW_MANUAL_REVIEW"
        assert review.retained_prefix_sha256 != review.observed_prefix_sha256
    else:
        assert review.disposition == "LOCAL_UNCHANGED_REVIEW"
        assert review.retained_prefix_sha256 == review.observed_prefix_sha256
        assert store.get(original.memory_id, scope, include_expired=True) == original

    assert store.events(other_scope) == other_events
    assert store.get(other.memory_id, other_scope, include_expired=True) == other
    assert len(store.events(scope)) == len(original_events) + int(target_updated)
    assert review.automatic_retry_authorized is False
    assert review.caller_commit_authenticated is False
    assert review.write_authorized is False
