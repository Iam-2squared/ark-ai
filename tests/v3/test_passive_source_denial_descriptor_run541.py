"""Passive V3 syntax-only transition cannot mutate source review authority.

Even a False-only property rebinding invalidates the retained review epoch.
No Candidate, training, GPU, budget or protected evaluation is authorized.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as transition

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("target", (
    "promotion_authorized",
    "v2_opening_authorized",
    "real_training_authorized",
))
def test_final_false_transition_getter_cannot_rebind_shape_authority(
    monkeypatch, target,
):
    def rebind(self):
        monkeypatch.setattr(
            transition.UnapprovedSnapshotShapeReview,
            target, property(lambda self: False),
        )
        return False

    monkeypatch.setattr(
        transition.PassiveReadinessTransition,
        "human_approval_verified", property(rebind),
    )
    with pytest.raises(
        transition.PassiveTransitionRejected, match="source report authority changed",
    ):
        transition.review_passive_readiness_transition(_snapshot(), _snapshot())


@pytest.mark.parametrize("target", ("promotion_authorized", "preflight_authorized"))
def test_last_reinspection_callback_cannot_rebind_shape_authority(
    monkeypatch, target,
):
    native = transition.review_unapproved_v3_snapshot_shapes
    count = 0

    def rebind_after_valid_review(snapshot):
        nonlocal count
        result = native(snapshot)
        count += 1
        if count == 4:
            monkeypatch.setattr(
                transition.UnapprovedSnapshotShapeReview, target,
                property(lambda self: False),
            )
        return result

    monkeypatch.setattr(
        transition, "review_unapproved_v3_snapshot_shapes", rebind_after_valid_review,
    )
    with pytest.raises(
        transition.PassiveTransitionRejected, match="source report authority changed",
    ):
        transition.review_passive_readiness_transition(_snapshot(), _snapshot())
    assert count == 4


def test_unapproved_transition_without_descriptor_drift_is_still_inert():
    before, after = _snapshot(), _snapshot()
    after["base"]["revision"] = "a" * 40
    report = transition.review_passive_readiness_transition(before, after)
    assert report.newly_plausible_paths == (
        "base.revision", "tokenizer.revision",
    )
    assert report.real_training_authorized is False
    assert report.protected_v2_authorized is False
    assert report.human_approval_verified is False
