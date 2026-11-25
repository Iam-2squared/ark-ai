"""Unapproved V3 syntax reports refuse preinstalled authority substitutions.

Only the committed local template is read for the untouched success case.
No Candidate, payment, training, model loading, or approval is attempted.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as transition

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


@pytest.mark.parametrize("denial", transition._DENIED)
def test_preinstalled_false_only_denial_rejected_before_snapshot_inspection(
    monkeypatch, denial,
):
    observed = []

    def forbidden(_value):
        observed.append("snapshot parsed")
        raise AssertionError("replaced passive authority must fail first")

    monkeypatch.setattr(transition, "_pin_json_tree", forbidden)
    monkeypatch.setattr(
        transition.PassiveReadinessTransition,
        denial,
        property(lambda _result: False),
    )
    with pytest.raises(transition.PassiveTransitionRejected, match="original passive"):
        transition.review_passive_readiness_transition({}, {})
    assert observed == []


def test_rebound_passive_result_type_rejected_before_snapshot_inspection(monkeypatch):
    observed = []

    def forbidden(_value):
        observed.append("snapshot parsed")
        raise AssertionError("substitute result class must fail first")

    monkeypatch.setattr(transition, "_pin_json_tree", forbidden)
    monkeypatch.setattr(transition, "PassiveReadinessTransition", object)
    with pytest.raises(transition.PassiveTransitionRejected, match="original passive"):
        transition.review_passive_readiness_transition({}, {})
    assert observed == []


def test_original_passive_review_remains_syntax_only():
    snapshot = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    report = transition.review_passive_readiness_transition(snapshot, snapshot)
    assert report.newly_plausible_paths == ()
    assert report.transition_sha256
    assert all(getattr(report, denial) is False for denial in transition._DENIED)
