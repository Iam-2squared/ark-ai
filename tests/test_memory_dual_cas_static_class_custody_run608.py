"""Manual dual Memory CAS review never invokes spoofed class authority getters."""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as mod


class ExplosiveDescriptor:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, _instance, _owner=None):
        self.calls.append("executed")
        return False


@pytest.mark.parametrize("group,name", (
    [("triage", name) for name in mod._TRIAGE_DENIALS]
    + [("outcome", name) for name in mod._OUTCOME_DENIALS]
    + [("pair", name) for name in mod._DENIALS]
))
def test_forged_false_getter_denied_without_execution(
    tmp_path, monkeypatch, group, name,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    target = {
        "triage": mod._TRIAGE,
        "outcome": mod._OUTCOME,
        "pair": mod._RESULT,
    }[group]
    called = []
    monkeypatch.setattr(target, name, ExplosiveDescriptor(called))
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="authority changed"):
        mod.review_memory_ambiguous_commit_pair(store, proposed, retained=retained)
    assert called == []


@pytest.mark.parametrize("group", ("triage", "outcome", "pair"))
def test_replaced_report_class_denied_before_reviewer_call(
    tmp_path, monkeypatch, group,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    called = []

    def forbidden(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("reviewer must not run")

    if group == "triage":
        monkeypatch.setattr(mod.triage_module, "MemoryCommitTriage", object)
    elif group == "outcome":
        monkeypatch.setattr(mod.outcome_module, "MemoryCASOutcomeReview", object)
    else:
        monkeypatch.setattr(mod, "MemoryAmbiguityPair", object)
    monkeypatch.setattr(mod, "_TRIAGE_FN", forbidden)
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="authority changed"):
        mod.review_memory_ambiguous_commit_pair(store, proposed, retained=retained)
    assert called == []


def test_callback_installed_getter_is_rejected_before_second_reviewer(
    tmp_path, monkeypatch,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    native = mod._TRIAGE_FN
    called = []

    def first(*args, **kwargs):
        result = native(*args, **kwargs)
        monkeypatch.setattr(
            mod._OUTCOME, "consent_authenticated", ExplosiveDescriptor(called),
        )
        return result

    monkeypatch.setattr(mod, "_TRIAGE_FN", first)
    monkeypatch.setattr(mod.triage_module, "review_uncertain_memory_commit", first)
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="authority changed"):
        mod.review_memory_ambiguous_commit_pair(store, proposed, retained=retained)
    assert called == []


def test_unmodified_manual_cas_pair_never_allows_retry(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    review = mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    assert review.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert review.automatic_retry_authorized is False
    assert review.caller_commit_authenticated is False
