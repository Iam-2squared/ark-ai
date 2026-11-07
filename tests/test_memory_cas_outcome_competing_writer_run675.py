"""Independent local writers cannot be attributed by CAS outcome observation.

All SQLite connections are offline fixtures. A matching post-COMMIT image,
even with exactly one new event, is never a proof of this caller's write or
an authorization to retry, disclose data, change retention, or dispatch.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    MemoryCASOutcomeRejected,
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _pair(tmp_path):
    path = tmp_path / "competing-writers.sqlite"
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    other_writer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-owner", "private")
    original = reader.put(MemoryWrite(scope, "source", "old"))
    retained = observe_memory_generation_for_cas(reader, scope, "source")
    return reader, other_writer, scope, original, retained


def _no_authority(outcome):
    assert outcome.commit_attributed_to_caller is False
    assert outcome.automatic_retry_authorized is False
    assert outcome.consent_authenticated is False
    assert outcome.trusted_clock_verified is False
    assert outcome.external_action_authorized is False


def test_independent_writer_matching_exact_proposal_is_not_caller_commit(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    proposal = MemoryWrite(
        scope, "source", "identical private bytes",
        metadata={"purpose": "fixture"}, expires_at_ms=1400,
    )
    committed = generation_fenced_memory_update(other, proposal, retained=retained)
    before = tuple(reader.events(scope))

    result = review_memory_generation_cas_outcome(
        reader, proposal, retained=retained,
    )

    assert result.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    _no_authority(result)
    assert committed.revision == original.revision + 1
    assert reader.get(original.memory_id, scope, include_expired=True) == committed
    assert tuple(reader.events(scope)) == before
    assert review_memory_generation_cas_outcome(
        reader, proposal, retained=retained,
    ) == result


@pytest.mark.parametrize(
    ("written", "proposed"),
    (
        (
            MemoryWrite(MemoryScope("fixture-owner", "private"), "source", "actual"),
            MemoryWrite(MemoryScope("fixture-owner", "private"), "source", "proposed"),
        ),
        (
            MemoryWrite(
                MemoryScope("fixture-owner", "private"), "source", "same",
                metadata={"writer": "independent"},
            ),
            MemoryWrite(
                MemoryScope("fixture-owner", "private"), "source", "same",
                metadata={"writer": "caller"},
            ),
        ),
        (
            MemoryWrite(
                MemoryScope("fixture-owner", "private"), "source", "same",
                expires_at_ms=1300,
            ),
            MemoryWrite(
                MemoryScope("fixture-owner", "private"), "source", "same",
                expires_at_ms=1500,
            ),
        ),
    ),
)
def test_independent_writer_different_payload_or_retention_never_matches(
    tmp_path, written, proposed,
):
    reader, other, scope, original, retained = _pair(tmp_path)
    latest = generation_fenced_memory_update(other, written, retained=retained)
    before = tuple(reader.events(scope))

    outcome = review_memory_generation_cas_outcome(
        reader, proposed, retained=retained,
    )
    assert outcome.observation == "DIVERGED_OBSERVED"
    _no_authority(outcome)
    assert latest.memory_id == original.memory_id
    assert reader.get(original.memory_id, scope, include_expired=True) == latest
    assert tuple(reader.events(scope)) == before


def test_other_rows_append_does_not_claim_a_commit_to_retained_row(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    other.put(MemoryWrite(scope, "independent-id", "unrelated private data"))
    before = tuple(reader.events(scope))

    result = review_memory_generation_cas_outcome(
        reader, MemoryWrite(scope, "source", "new"),
        retained=retained,
    )
    assert result.observation == "UNCHANGED_OBSERVED"
    _no_authority(result)
    assert reader.get(original.memory_id, scope, include_expired=True) == original
    assert tuple(reader.events(scope)) == before


def test_recreated_same_memory_id_requires_manual_review_not_replay(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    assert other.delete(original.memory_id, scope, expected_revision=1)
    replacement = other.put(
        MemoryWrite(scope, "source", "new lifetime"), expected_revision=0,
    )
    before = tuple(reader.events(scope))

    with pytest.raises(MemoryCASOutcomeRejected):
        review_memory_generation_cas_outcome(
            reader, MemoryWrite(scope, "source", "new lifetime"),
            retained=retained,
        )

    assert replacement.memory_id == original.memory_id
    assert replacement.revision == 1
    assert tuple(reader.events(scope)) == before
    assert reader.get(original.memory_id, scope, include_expired=True) == replacement


def test_two_competing_updates_with_identical_last_bytes_are_not_one_commit(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    proposal = MemoryWrite(
        scope, "source", "matching latest", metadata={"mode": "local"},
    )
    first = generation_fenced_memory_update(other, proposal, retained=retained)
    next_token = observe_memory_generation_for_cas(other, scope, "source")
    latest = generation_fenced_memory_update(
        other, proposal, retained=next_token,
    )
    before = tuple(reader.events(scope))

    result = review_memory_generation_cas_outcome(
        reader, proposal, retained=retained,
    )

    assert first.revision == original.revision + 1
    assert latest.revision == original.revision + 2
    assert result.observation == "DIVERGED_OBSERVED"
    _no_authority(result)
    assert reader.get(original.memory_id, scope, include_expired=True) == latest
    assert tuple(reader.events(scope)) == before


def test_identical_source_in_other_scope_does_not_advance_retained_row(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    another_scope = MemoryScope(scope.owner_id, "fixture-other-namespace")
    other.put(MemoryWrite(another_scope, "source", "other private data"))
    before = tuple(reader.events(scope))

    result = review_memory_generation_cas_outcome(
        reader, MemoryWrite(scope, "source", "proposed"),
        retained=retained,
    )

    assert result.observation == "UNCHANGED_OBSERVED"
    _no_authority(result)
    assert reader.get(original.memory_id, scope, include_expired=True) == original
    assert tuple(reader.events(scope)) == before


def test_removed_row_without_recreation_is_manual_only(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    assert other.delete(original.memory_id, scope, expected_revision=1)
    before = tuple(reader.events(scope))

    with pytest.raises(MemoryCASOutcomeRejected):
        review_memory_generation_cas_outcome(
            reader, MemoryWrite(scope, "source", "no replay"),
            retained=retained,
        )

    assert tuple(reader.events(scope)) == before
    assert reader.get(original.memory_id, scope, include_expired=True) is None


def test_reopened_reader_cannot_attribute_competing_matching_update(tmp_path):
    reader, other, scope, original, retained = _pair(tmp_path)
    proposal = MemoryWrite(
        scope, "source", "restart-stable fixture", expires_at_ms=1500,
    )
    expected = generation_fenced_memory_update(other, proposal, retained=retained)
    restarted = SQLiteMemoryStore(tmp_path / "competing-writers.sqlite",
                                  clock_ms=lambda: 1000)
    before = tuple(restarted.events(scope))

    result = review_memory_generation_cas_outcome(
        restarted, proposal, retained=retained,
    )

    assert result.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    _no_authority(result)
    assert restarted.get(
        original.memory_id, scope, include_expired=True,
    ) == expected
    assert tuple(restarted.events(scope)) == before
