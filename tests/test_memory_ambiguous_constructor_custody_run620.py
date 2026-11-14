"""Ambiguous Memory COMMIT reconciliation cannot execute a forged constructor.

Two local read-only observers never prove caller authorship, consent, time,
retry safety, external effects, or even an atomic cross-process snapshot.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as pair
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


@pytest.mark.parametrize("matching_update", (False, True))
def test_preinstalled_result_constructor_denied_before_sqlite(
    tmp_path, monkeypatch, matching_update,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    if matching_update:
        generation_fenced_memory_update(store, proposed, retained=retained)
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("invoked")
        raise AssertionError("counterfeit constructor must not execute")

    def sqlite_forbidden(*_args, **_kwargs):
        raise AssertionError("no SQLite review may start with forged constructor")

    with monkeypatch.context() as patch:
        patch.setattr(pair.MemoryAmbiguityPair, "__init__", forbidden)
        patch.setattr(type(store), "_connect_readonly", sqlite_forbidden)
        with pytest.raises(pair.MemoryAmbiguityPairRejected, match="authority changed"):
            pair.review_memory_ambiguous_commit_pair(
                store, proposed, retained=retained,
            )

    assert attempted == []


@pytest.mark.parametrize("child", ("triage", "outcome"))
def test_reentrant_observer_replaces_constructor_before_result(
    tmp_path, monkeypatch, child,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    if child == "triage":
        original = pair._TRIAGE_FN
        module = pair.triage_module
        name = "review_uncertain_memory_commit"
        alias = "_TRIAGE_FN"
    else:
        original = pair._OUTCOME_FN
        module = pair.outcome_module
        name = "review_memory_generation_cas_outcome"
        alias = "_OUTCOME_FN"
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("invoked")
        raise AssertionError("counterfeit constructor must not execute")

    with monkeypatch.context() as patch:
        def observer_hook(*args, **kwargs):
            actual = original(*args, **kwargs)
            patch.setattr(pair.MemoryAmbiguityPair, "__init__", forbidden)
            return actual

        patch.setattr(pair, alias, observer_hook)
        patch.setattr(module, name, observer_hook)
        with pytest.raises(pair.MemoryAmbiguityPairRejected, match="authority changed"):
            pair.review_memory_ambiguous_commit_pair(
                store, proposed, retained=retained,
            )

    assert attempted == []


def test_original_reconciliation_remains_read_only_and_non_authorizing(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    report = pair.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert report.caller_commit_authenticated is False
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.trusted_clock_verified is False
