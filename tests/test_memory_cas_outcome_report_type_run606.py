"""CAS manual review must pin its report class, not only inherited denials.

These synthetic cases use temporary local Memory databases. A counterfeit
class which reuses the original False-valued descriptors is still untrusted.
"""

from __future__ import annotations

import pytest
from test_memory_generation_cas_outcome_run536 import _case

from ark.memory import generation_cas_outcome_review as outcome

_FLAGS = (
    "commit_attributed_to_caller",
    "automatic_retry_authorized",
    "consent_authenticated",
    "trusted_clock_verified",
    "external_action_authorized",
)


def _counterfeit(constructor_calls):
    original = outcome.MemoryCASOutcomeReview

    def fraudulent_constructor(self, *args):
        constructor_calls.append(args)

    namespace = {name: vars(original)[name] for name in _FLAGS}
    namespace["__init__"] = fraudulent_constructor
    return type("CounterfeitCASOutcomeReview", (), namespace)


def test_preinstalled_same_descriptor_class_rejected_before_sqlite(
    tmp_path, monkeypatch,
):
    store, _, _, retained, proposed = _case(tmp_path)
    calls = []
    opened = []

    def forbidden_read(self):
        opened.append(True)
        raise AssertionError("SQLite must not open for counterfeit report class")

    monkeypatch.setattr(type(store), "_connect_readonly", forbidden_read)
    monkeypatch.setattr(
        outcome, "MemoryCASOutcomeReview", _counterfeit(calls),
    )
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected,
        match="authority definition changed",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert calls == []
    assert opened == []


def test_same_descriptor_class_swapped_inside_snapshot_never_constructed(
    tmp_path, monkeypatch,
):
    store, _, _, retained, proposed = _case(tmp_path)
    calls = []
    counterfeit = _counterfeit(calls)
    original_snapshot = outcome._snapshot
    replaced = []

    def swap_after_snapshot(*args, **kwargs):
        record, token = original_snapshot(*args, **kwargs)
        if not replaced:
            replaced.append(True)
            monkeypatch.setattr(outcome, "MemoryCASOutcomeReview", counterfeit)
        return record, token

    monkeypatch.setattr(outcome, "_snapshot", swap_after_snapshot)
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected, match="manual inspection required",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert replaced == [True]
    assert calls == []


def test_normal_report_stays_deny_only(tmp_path):
    store, _, _, retained, proposed = _case(tmp_path)
    report = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert type(report) is outcome.MemoryCASOutcomeReview
    assert report.observation == "UNCHANGED_OBSERVED"
    assert all(getattr(report, name) is False for name in _FLAGS)
