"""Manual CAS outcome must reject replaced deny-only code before any DB read."""

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


@pytest.mark.parametrize("flag", _FLAGS)
def test_preinstalled_false_only_denial_cannot_start_local_triage(
    tmp_path, monkeypatch, flag,
):
    store, _, _, retained, proposed = _case(tmp_path)
    opened = []

    def forbidden_read(self):
        opened.append(True)
        raise AssertionError("no SQLite observation before checking original denials")

    monkeypatch.setattr(type(store), "_connect_readonly", forbidden_read)
    monkeypatch.setattr(
        outcome.MemoryCASOutcomeReview,
        flag, property(lambda _self: False),
    )
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected, match="authority definition changed",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert opened == []


def test_late_descriptor_replacement_is_quarantined_during_first_snapshot(
    tmp_path, monkeypatch,
):
    store, _, _, retained, proposed = _case(tmp_path)
    original_snapshot = outcome._snapshot
    calls = []

    def swap_after_snapshot(*args, **kwargs):
        row, token = original_snapshot(*args, **kwargs)
        if not calls:
            calls.append("snapshot")
            monkeypatch.setattr(
                outcome.MemoryCASOutcomeReview,
                "external_action_authorized",
                property(lambda _self: False),
            )
        return row, token

    monkeypatch.setattr(outcome, "_snapshot", swap_after_snapshot)
    # Inside the read-only snapshot transaction, the precise denial is
    # normalized to the manual-inspection blocker; no output is returned.
    with pytest.raises(
        outcome.MemoryCASOutcomeRejected, match="manual inspection required",
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert calls == ["snapshot"]


def test_unmodified_cas_outcome_remains_manual_only(tmp_path):
    store, _, _, retained, proposed = _case(tmp_path)
    result = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert result.observation == "UNCHANGED_OBSERVED"
    for flag in _FLAGS:
        assert getattr(result, flag) is False
