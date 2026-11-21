"""Independent SQLite writers cannot confer COMMIT-UNKNOWN caller identity.

Only local row/event evidence is reviewed. All outcomes stay diagnostic,
never attribution, consent, a trusted clock or authorization to retry.
"""

from __future__ import annotations

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    review_memory_ambiguous_commit_pair,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _case(tmp_path):
    path = tmp_path / "independent-author.sqlite"
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("private-fixture-owner", "offline")
    original = observer.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(observer, scope, "source")
    proposed = MemoryWrite(
        scope, "source", "same proposed bytes",
        metadata={"review": "manual"}, expires_at_ms=2000,
    )
    return observer, writer, scope, original.memory_id, retained, proposed


def _assert_non_authorizing(report):
    assert report.caller_commit_authenticated is False
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.trusted_clock_verified is False
    assert len(report.reconciliation_sha256) == 64


def test_an_independent_matching_writer_is_visible_not_attributed(tmp_path):
    observer, writer, scope, memory_id, retained, proposed = _case(tmp_path)
    generation_fenced_memory_update(writer, proposed, retained=retained)
    before_events = observer.events(scope)
    before_record = observer.get(memory_id, scope, include_expired=True)

    report = review_memory_ambiguous_commit_pair(
        observer, proposed, retained=retained,
    )
    assert report.disposition == "MATCHING_ROW_MANUAL_REVIEW"
    assert report.retained_prefix_sha256 != report.observed_prefix_sha256
    _assert_non_authorizing(report)
    assert observer.events(scope) == before_events
    assert observer.get(memory_id, scope, include_expired=True) == before_record
    assert before_record.revision == 2


def test_two_independent_identical_updates_are_not_one_occurrence(tmp_path):
    observer, writer, scope, memory_id, retained, proposed = _case(tmp_path)
    generation_fenced_memory_update(writer, proposed, retained=retained)
    newer = observe_memory_generation_for_cas(writer, scope, "source")
    generation_fenced_memory_update(writer, proposed, retained=newer)
    before_events = observer.events(scope)

    report = review_memory_ambiguous_commit_pair(
        observer, proposed, retained=retained,
    )
    assert report.disposition == "DIVERGED_MANUAL_REVIEW"
    _assert_non_authorizing(report)
    assert observer.events(scope) == before_events
    assert observer.get(memory_id, scope, include_expired=True).revision == 3


def test_independent_writer_of_unrelated_scope_does_not_attrib_same_row(tmp_path):
    observer, writer, scope, memory_id, retained, proposed = _case(tmp_path)
    unrelated = MemoryScope("other-fixture-owner", "offline")
    writer.put(MemoryWrite(unrelated, "another-source", "separate payload"))
    generation_fenced_memory_update(writer, proposed, retained=retained)

    prior_events = observer.events(scope)
    report = review_memory_ambiguous_commit_pair(
        observer, proposed, retained=retained,
    )
    assert report.disposition == "MATCHING_ROW_MANUAL_REVIEW"
    _assert_non_authorizing(report)
    assert observer.events(scope) == prior_events
    assert observer.get(memory_id, scope, include_expired=True).revision == 2
