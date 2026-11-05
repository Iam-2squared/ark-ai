"""CAS ambiguous-outcome read-only receipts reject executable result carriers.

Each test uses disposable local SQLite. A forged field descriptor or attribute
hook must be refused before opening private records; post-snapshot mutation
remains a manual-only diagnostic blocker, never authority to retry a WRITE.
"""

from __future__ import annotations

import pytest
from test_memory_generation_cas_outcome_run536 import _case

from ark.memory import generation_cas_outcome_review as outcome

_FIELDS = (
    "observation",
    "retained_prefix_sha256",
    "observed_prefix_sha256",
    "observed_row_sha256",
    "expected_content_sha256",
    "review_sha256",
)


@pytest.mark.parametrize("field", _FIELDS)
def test_preinstalled_forged_result_slot_rejected_before_sqlite(
    tmp_path, monkeypatch, field,
):
    store, _, _, retained, proposed = _case(tmp_path)
    accessed = []

    def forged_getter(_self):
        accessed.append(field)
        raise AssertionError("forged result descriptor must not execute")

    def forbidden_open(_self):
        raise AssertionError("private SQLite read must be blocked by preflight")

    monkeypatch.setattr(type(store), "_connect_readonly", forbidden_open)
    monkeypatch.setattr(outcome.MemoryCASOutcomeReview, field, property(forged_getter))
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected, match="authority definition changed",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert accessed == []


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_preinstalled_executable_lookup_hook_never_runs(
    tmp_path, monkeypatch, hook,
):
    store, _, _, retained, proposed = _case(tmp_path)
    called = []

    def forbidden_hook(_self, _name):
        called.append(_name)
        raise AssertionError("forged attribute hook must not execute")

    def forbidden_open(_self):
        raise AssertionError("private SQLite read must be blocked by preflight")

    monkeypatch.setattr(type(store), "_connect_readonly", forbidden_open)
    monkeypatch.setattr(
        outcome.MemoryCASOutcomeReview, hook, forbidden_hook, raising=False,
    )
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected, match="authority definition changed",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert called == []


def test_result_field_swapped_during_snapshot_is_manual_only(
    tmp_path, monkeypatch,
):
    store, _, _, retained, proposed = _case(tmp_path)
    native_snapshot = outcome._snapshot
    calls = []

    def swap_after_snapshot(*args, **kwargs):
        record, observed = native_snapshot(*args, **kwargs)
        if not calls:
            calls.append(True)
            monkeypatch.setattr(
                outcome.MemoryCASOutcomeReview,
                "review_sha256",
                property(lambda _self: "0" * 64),
            )
        return record, observed

    monkeypatch.setattr(outcome, "_snapshot", swap_after_snapshot)
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected, match="manual inspection required",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert calls == [True]
