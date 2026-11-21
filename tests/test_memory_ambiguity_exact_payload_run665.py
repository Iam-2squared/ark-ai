"""Unattributed SQLite matching content is not a matching Memory write.

Only complete proposed content, metadata and expiry can be locally compared.
Synthetic read-only ambiguity reports are never writer attribution or replay
authority. These fixtures do not dispatch any real tool or notification.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    review_memory_ambiguous_commit_pair,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("proposed_content", "proposed_metadata", "proposed_expiry",
     "written_content", "written_metadata", "written_expiry"),
    [
        ("same", {"label": "private"}, 1500,
         "same", {"label": "public"}, 1500),
        ("same", {"label": "private"}, 1500,
         "same", {"label": "private"}, 1400),
        ("caf\u00e9", {"label": "private"}, 1500,
         "cafe\u0301", {"label": "private"}, 1500),
    ],
    ids=["metadata-not-attributed", "expiry-not-attributed",
         "unicode-bytes-not-attributed"],
)
def test_matching_appearance_never_proves_caller_payload(
    tmp_path, proposed_content, proposed_metadata, proposed_expiry,
    written_content, written_metadata, written_expiry,
):
    path = tmp_path / "unknown-author.sqlite"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    independent_writer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-private-owner", "fixture")
    original = reader.put(MemoryWrite(scope, "one-source", "initial"))
    retained = observe_memory_generation_for_cas(reader, scope, "one-source")

    proposed = MemoryWrite(
        scope, "one-source", proposed_content,
        proposed_metadata, expires_at_ms=proposed_expiry,
    )
    actual = MemoryWrite(
        scope, "one-source", written_content,
        written_metadata, expires_at_ms=written_expiry,
    )
    generation_fenced_memory_update(
        independent_writer, actual, retained=retained,
    )

    before_events = reader.events(scope)
    before_row = reader.get(original.memory_id, scope, include_expired=True)
    result = review_memory_ambiguous_commit_pair(
        reader, proposed, retained=retained,
    )
    assert result.disposition == "DIVERGED_MANUAL_REVIEW"
    assert result.caller_commit_authenticated is False
    assert result.automatic_retry_authorized is False
    assert result.write_authorized is False
    assert result.trusted_clock_verified is False
    assert len(result.reconciliation_sha256) == 64
    assert reader.events(scope) == before_events
    assert reader.get(original.memory_id, scope, include_expired=True) == before_row
    assert before_row.revision == 2
    assert before_row.content == written_content
    assert dict(before_row.metadata) == written_metadata
    assert before_row.expires_at_ms == written_expiry
