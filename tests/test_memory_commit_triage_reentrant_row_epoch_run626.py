"""A manual COMMIT-UNKNOWN review must bind its original SQLite row image.

Only disposable local Memory fixtures are used. Neither an observed matching
row nor an inert receipt attributes a commit or permits another write.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import postcommit_uncertainty_review as triage


@pytest.mark.parametrize("digest_call", (1, 2))
@pytest.mark.parametrize("field", ("content", "revision", "metadata"))
def test_row_mutated_after_digest_is_not_a_commit_match(
    tmp_path, monkeypatch, digest_call, field,
):
    store, scope, original_record, retained, proposed = make_case(tmp_path)
    hash_before = triage._row_hash
    calls = []

    def reentrant_hash(record):
        digest = hash_before(record)
        calls.append("row digest")
        if len(calls) == digest_call:
            if field == "content":
                # A stale hash could otherwise conceal a forged match.
                object.__setattr__(record, field, proposed.content)
            elif field == "revision":
                object.__setattr__(record, field, record.revision + 1)
            else:
                object.__setattr__(record, field, {"source": "changed"})
        return digest

    with monkeypatch.context() as patch:
        patch.setattr(triage, "_row_hash", reentrant_hash)
        with pytest.raises(
            triage.MemoryCommitTriageRejected,
            match="manual review required",
        ) as denial:
            triage.review_uncertain_memory_commit(
                store, proposed, retained_before=retained,
            )
    # The public API intentionally obscures the exact internal fault while
    # retaining a cause for local testing. Neither error permits a retry.
    assert isinstance(denial.value.__cause__, triage.MemoryCommitTriageRejected)
    assert "row image changed after snapshot" in str(denial.value.__cause__)
    assert len(calls) >= digest_call
    assert store.get(original_record.memory_id, scope).content == "original"
    assert [event.operation for event in store.events(scope)] == ["create"]


@pytest.mark.parametrize("has_matching_update", (False, True))
def test_normal_review_stays_manual_only(tmp_path, has_matching_update):
    from ark.memory.generation_fenced_cas import generation_fenced_memory_update

    store, _, _, retained, proposed = make_case(tmp_path)
    if has_matching_update:
        generation_fenced_memory_update(store, proposed, retained=retained)
    report = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == (
        "ONE_MATCHING_UPDATE_VISIBLE" if has_matching_update
        else "LOCAL_UNCHANGED"
    )
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
