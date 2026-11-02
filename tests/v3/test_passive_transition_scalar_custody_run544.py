"""Unapproved V3 reinspection must not rely on replaceable report equality.

This is a passive syntax-only fixture: no model, Candidate or paid action.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as transition

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


@pytest.mark.parametrize("comparison", ("always_true", "always_false", "raises"))
def test_passive_transition_field_recheck_ignores_patched_shape_equality(
    monkeypatch, comparison,
):
    before = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    after = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    after["base"]["revision"] = "a" * 40

    def poisoned_eq(self, other):
        if comparison == "raises":
            raise AssertionError("source report equality must not be called")
        return comparison == "always_true"

    with monkeypatch.context() as patch:
        patch.setattr(
            transition.UnapprovedSnapshotShapeReview, "__eq__", poisoned_eq,
        )
        report = transition.review_passive_readiness_transition(before, after)

    assert report.newly_plausible_paths == (
        "base.revision", "tokenizer.revision",
    )
    assert report.newly_malformed_paths == ()
    assert report.artifact_identity_verified is False
    assert report.human_approval_verified is False
    assert report.real_training_authorized is False
    assert report.external_compute_authorized is False
