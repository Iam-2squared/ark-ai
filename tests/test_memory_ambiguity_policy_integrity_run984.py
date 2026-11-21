"""Detached Memory COMMIT ambiguity policy must be immutable per review.

No retry, attribution or operation; disposable SQLite fixtures only.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as mod


def _attempt(case):
    store, _, _, retained, proposed = case
    return mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )


def _deny_any_database_read(store, patch):
    def forbidden(*args, **kwargs):
        raise AssertionError("mutated reconciliation policy reached SQLite")

    patch.setattr(type(store), "_connect_readonly", forbidden)


@pytest.mark.parametrize(
    "name",
    (
        "_TRIAGE_DENIALS", "_OUTCOME_DENIALS", "_DENIALS",
        "_RESULT_FIELDS", "_TRIAGE_FIELDS", "_OUTCOME_FIELDS",
        "_CARRIER_HOOKS", "_ORIGINAL_RESULT_FIELDS",
        "_ORIGINAL_TRIAGE_FIELDS", "_ORIGINAL_OUTCOME_FIELDS",
        "_ORIGINAL_RESULT_HOOKS", "_ORIGINAL_TRIAGE_HOOKS",
        "_ORIGINAL_OUTCOME_HOOKS", "_TRIAGE_ORIGINALS",
        "_OUTCOME_ORIGINALS", "_ORIGINALS",
    ),
)
@pytest.mark.parametrize("mutation", ("truncate", "equal_rebind"))
def test_memory_ambiguity_vector_substitution_refused_before_sqlite(
    tmp_path, monkeypatch, name, mutation,
):
    case = make_case(tmp_path)
    old = getattr(mod, name)
    replacement = old[:-1] if mutation == "truncate" else tuple(list(old))
    assert replacement is not old
    with monkeypatch.context() as patch:
        _deny_any_database_read(case[0], patch)
        patch.setattr(mod, name, replacement)
        with pytest.raises(
            mod.MemoryAmbiguityPairRejected,
            match="digest implementation or domain changed",
        ):
            _attempt(case)


@pytest.mark.parametrize("mutation", (
    "equal_rebind", "remove_mapping", "change_disposition", "add_cross_pair",
))
def test_memory_ambiguity_disposition_policy_cannot_be_mutated(
    tmp_path, monkeypatch, mutation,
):
    case = make_case(tmp_path)
    policy = dict(mod._DISPOSITIONS)
    if mutation == "remove_mapping":
        del policy[("LOCAL_UNCHANGED", "UNCHANGED_OBSERVED")]
    elif mutation == "change_disposition":
        policy[("LOCAL_UNCHANGED", "UNCHANGED_OBSERVED")] = "AUTO_RETRY"
    elif mutation == "add_cross_pair":
        policy[("LOCAL_UNCHANGED", "DIVERGED_OBSERVED")] = "LOCAL_UNCHANGED_REVIEW"
    with monkeypatch.context() as patch:
        _deny_any_database_read(case[0], patch)
        if mutation == "equal_rebind":
            patch.setattr(mod, "_DISPOSITIONS", policy)
        else:
            # Mutate the original dict in place to ensure the frozen row
            # snapshot catches changes even when map identity still matches.
            patch.setattr(mod, "_DISPOSITIONS", policy)
            patch.setattr(mod, "_ORIGINAL_DISPOSITION_MAP", policy)
        with pytest.raises(
            mod.MemoryAmbiguityPairRejected,
            match="digest implementation or domain changed",
        ):
            _attempt(case)


def test_memory_ambiguity_normal_manual_review_retains_all_denials(tmp_path):
    result = _attempt(make_case(tmp_path))
    assert result.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert result.caller_commit_authenticated is False
    assert result.automatic_retry_authorized is False
    assert result.write_authorized is False
    assert result.trusted_clock_verified is False
