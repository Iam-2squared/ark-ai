"""Dual Memory ambiguity reviewers cannot launder a changed child receipt.

Only synthetic local SQLite histories are used. A matching row is not an
authenticated COMMIT and no assertion here authorizes retry or disclosure.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as mod
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


def _pair(case):
    store, _, _, retained, proposed = case
    return mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )


@pytest.mark.parametrize("child", ("triage", "outcome"))
def test_forged_child_receipt_digest_cannot_be_laundered_into_pair(
    tmp_path, monkeypatch, child,
):
    case = make_case(tmp_path)
    if child == "triage":
        native = mod._TRIAGE_FN

        def forged(*args, **kwargs):
            return replace(native(*args, **kwargs), report_sha256="f" * 64)

        monkeypatch.setattr(mod, "_TRIAGE_FN", forged)
        monkeypatch.setattr(
            mod.triage_module, "review_uncertain_memory_commit", forged,
        )
    else:
        native = mod._OUTCOME_FN

        def forged(*args, **kwargs):
            return replace(native(*args, **kwargs), review_sha256="f" * 64)

        monkeypatch.setattr(mod, "_OUTCOME_FN", forged)
        monkeypatch.setattr(
            mod.outcome_module, "review_memory_generation_cas_outcome", forged,
        )
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="child digest mismatch"):
        _pair(case)


@pytest.mark.parametrize("field", ("report_sha256", "observed_prefix_sha256"))
def test_second_child_review_cannot_rewrite_first_child(
    tmp_path, monkeypatch, field,
):
    case = make_case(tmp_path)
    native_triage = mod._TRIAGE_FN
    native_outcome = mod._OUTCOME_FN
    observed = {}

    def capture(*args, **kwargs):
        receipt = native_triage(*args, **kwargs)
        observed["first"] = receipt
        return receipt

    def mutate_after_second(*args, **kwargs):
        receipt = native_outcome(*args, **kwargs)
        object.__setattr__(observed["first"], field, "f" * 64)
        return receipt

    monkeypatch.setattr(mod, "_TRIAGE_FN", capture)
    monkeypatch.setattr(
        mod.triage_module, "review_uncertain_memory_commit", capture,
    )
    monkeypatch.setattr(mod, "_OUTCOME_FN", mutate_after_second)
    monkeypatch.setattr(
        mod.outcome_module, "review_memory_generation_cas_outcome",
        mutate_after_second,
    )
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="child receipt changed"):
        _pair(case)


@pytest.mark.parametrize("updated", (False, True))
def test_untampered_child_receipts_keep_manual_only_triage(tmp_path, updated):
    case = make_case(tmp_path)
    if updated:
        store, _, _, retained, proposed = case
        generation_fenced_memory_update(store, proposed, retained=retained)
    result = _pair(case)
    assert result.disposition == (
        "MATCHING_ROW_MANUAL_REVIEW" if updated else "LOCAL_UNCHANGED_REVIEW"
    )
    assert result.automatic_retry_authorized is False
    assert result.write_authorized is False
    assert result.caller_commit_authenticated is False
