"""Read-only manual triage of locally ambiguous Memory CAS outcomes."""

from dataclasses import replace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.postcommit_uncertainty_review import (
    MemoryCommitTriage,
    MemoryCommitTriageRejected,
    review_uncertain_memory_commit,
)


def make_case(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "triage.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("offline-owner", "private")
    saved = store.put(
        MemoryWrite(scope, "stable", "original"), expected_revision=0,
    )
    retained = observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(
        scope, "stable", "updated", metadata={"source": "local"},
    )
    return store, scope, saved, retained, proposed


def test_unchanged_is_diagnostic_and_never_retry_permission(tmp_path):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    report = review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert type(report) is MemoryCommitTriage
    assert report.disposition == "LOCAL_UNCHANGED"
    assert report.retained_event_id == report.observed_event_id
    assert len(report.report_sha256) == 64
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
    assert report.trusted_clock_proven is False
    assert store.get(saved.memory_id, scope).content == "original"
    assert [x.operation for x in store.events(scope)] == ["create"]


def test_single_matching_update_is_visible_but_not_attributed(tmp_path):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    generation_fenced_memory_update(store, proposed, retained=retained)
    report = review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "ONE_MATCHING_UPDATE_VISIBLE"
    assert report.observed_event_id > report.retained_event_id
    assert report.observed_prefix_sha256 != report.retained_prefix_sha256
    assert report.automatic_retry_authorized is False
    assert report.caller_attribution_proven is False
    assert store.get(saved.memory_id, scope).revision == 2
    assert [x.operation for x in store.events(scope)] == ["create", "update"]


@pytest.mark.parametrize("different", ("other-content", "wrong-metadata", "wrong-expiry"))
def test_unrelated_local_image_cannot_be_called_matching(tmp_path, different):
    store, scope, _, retained, proposed = make_case(tmp_path)
    if different == "other-content":
        actual = MemoryWrite(scope, "stable", "other")
    elif different == "wrong-metadata":
        actual = MemoryWrite(scope, "stable", "updated", metadata={"source": "other"})
    else:
        actual = MemoryWrite(
            scope, "stable", "updated", metadata={"source": "local"},
            expires_at_ms=1500,
        )
    generation_fenced_memory_update(store, actual, retained=retained)
    report = review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "INDETERMINATE"
    assert report.automatic_retry_authorized is False


def test_two_updates_are_indeterminate_not_exactly_once(tmp_path):
    store, scope, _, retained, proposed = make_case(tmp_path)
    generation_fenced_memory_update(store, proposed, retained=retained)
    next_token = observe_memory_generation_for_cas(store, scope, "stable")
    generation_fenced_memory_update(store, proposed, retained=next_token)
    report = review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "INDETERMINATE"
    assert len(store.events(scope)) == 3


def test_deleted_and_recreated_row_does_not_match_old_generation(tmp_path):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    assert store.delete(saved.memory_id, scope, expected_revision=1)
    store.put(proposed, expected_revision=0)
    report = review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "INDETERMINATE"
    assert report.caller_attribution_proven is False


@pytest.mark.parametrize("field", ("event_prefix_sha256", "last_event_id"))
def test_forged_retained_prefix_is_rejected(tmp_path, field):
    store, _, _, retained, proposed = make_case(tmp_path)
    bad = replace(
        retained, **{field: "0" * 64 if field.endswith("sha256") else 999},
    )
    with pytest.raises(MemoryCommitTriageRejected):
        review_uncertain_memory_commit(store, proposed, retained_before=bad)


def test_retained_token_cannot_be_used_for_another_source(tmp_path):
    store, scope, _, retained, _ = make_case(tmp_path)
    with pytest.raises(MemoryCommitTriageRejected):
        review_uncertain_memory_commit(
            store, MemoryWrite(scope, "another", "other"),
            retained_before=retained,
        )


@pytest.mark.parametrize(
    "name", (
        "automatic_retry_authorized", "write_authorized",
        "caller_attribution_proven", "trusted_clock_proven",
    ),
)
def test_original_denials_are_required_before_local_triage(
    tmp_path, monkeypatch, name,
):
    from ark.memory import postcommit_uncertainty_review as triage

    store, _, _, retained, proposed = make_case(tmp_path)
    monkeypatch.setattr(
        triage.MemoryCommitTriage, name, property(lambda self: False),
    )
    with pytest.raises(MemoryCommitTriageRejected):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )


def test_no_row_after_delete_requires_manual_review(tmp_path):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    assert store.delete(saved.memory_id, scope, expected_revision=1)
    with pytest.raises(MemoryCommitTriageRejected, match="manual review"):
        review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
