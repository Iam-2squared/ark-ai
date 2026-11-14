"""Manual-only Memory COMMIT triage must never execute class getter shims.

Each fixture uses disposable SQLite. No automatic retry, user consent, or
attribution of an ambiguous commit is ever established by these reviews.
"""

import pytest
from test_memory_generation_cas_outcome_run536 import _case
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import generation_cas_outcome_review as outcome
from ark.memory import postcommit_uncertainty_review as triage


class CounterfeitDescriptor:
    def __init__(self, original, invoked):
        self.original = original
        self.invoked = invoked

    def __get__(self, instance, owner=None):
        self.invoked.append("executed")
        return self.original if instance is None else False


@pytest.mark.parametrize("flag", triage._DENIALS)
def test_triage_preinstalled_class_getter_is_not_executed(
    tmp_path, monkeypatch, flag,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    invoked = []
    original = vars(triage.MemoryCommitTriage)[flag]
    monkeypatch.setattr(
        triage.MemoryCommitTriage,
        flag,
        CounterfeitDescriptor(original, invoked),
    )
    with pytest.raises(triage.MemoryCommitTriageRejected):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert invoked == []


@pytest.mark.parametrize("flag", outcome._DENIED)
def test_cas_preinstalled_class_getter_is_not_executed(
    tmp_path, monkeypatch, flag,
):
    store, _, _, retained, proposed = _case(tmp_path)
    invoked = []
    original = vars(outcome.MemoryCASOutcomeReview)[flag]
    monkeypatch.setattr(
        outcome.MemoryCASOutcomeReview,
        flag,
        CounterfeitDescriptor(original, invoked),
    )
    with pytest.raises(outcome.MemoryCASOutcomeRejected):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert invoked == []


@pytest.mark.parametrize("flag", triage._DENIALS)
def test_triage_snapshot_callback_cannot_install_false_getter(
    tmp_path, monkeypatch, flag,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    invoked = []
    original = vars(triage.MemoryCommitTriage)[flag]
    read = triage._snapshot

    def injected(*args, **kwargs):
        result = read(*args, **kwargs)
        monkeypatch.setattr(
            triage.MemoryCommitTriage,
            flag,
            CounterfeitDescriptor(original, invoked),
        )
        return result

    monkeypatch.setattr(triage, "_snapshot", injected)
    with pytest.raises(triage.MemoryCommitTriageRejected):
        triage.review_uncertain_memory_commit(
            store, proposed, retained_before=retained,
        )
    assert invoked == []


@pytest.mark.parametrize("flag", outcome._DENIED)
def test_cas_snapshot_callback_cannot_install_false_getter(
    tmp_path, monkeypatch, flag,
):
    store, _, _, retained, proposed = _case(tmp_path)
    invoked = []
    original = vars(outcome.MemoryCASOutcomeReview)[flag]
    read = outcome._snapshot

    def injected(*args, **kwargs):
        result = read(*args, **kwargs)
        monkeypatch.setattr(
            outcome.MemoryCASOutcomeReview,
            flag,
            CounterfeitDescriptor(original, invoked),
        )
        return result

    monkeypatch.setattr(outcome, "_snapshot", injected)
    with pytest.raises(outcome.MemoryCASOutcomeRejected):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert invoked == []


def test_unmodified_triage_is_manual_only(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    receipt = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert receipt.disposition == "LOCAL_UNCHANGED"
    assert receipt.automatic_retry_authorized is False
    assert receipt.write_authorized is False


def test_unmodified_outcome_is_manual_only(tmp_path):
    store, _, _, retained, proposed = _case(tmp_path)
    receipt = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert receipt.observation == "UNCHANGED_OBSERVED"
    assert receipt.automatic_retry_authorized is False
    assert receipt.commit_attributed_to_caller is False
