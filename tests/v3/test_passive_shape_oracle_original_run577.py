"""Unapproved V3 syntax review must not trust a replaced shape oracle.

Only existing local placeholder JSON is read; no model, GPU, approval or
protected evaluation is requested by these negative tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as transition
from ark.learning import offline_snapshot_shape_review as shape


_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("target", ("independent", "child"))
def test_preinstalled_permissive_oracle_rejected_before_review(monkeypatch, target):
    module = transition if target == "independent" else shape
    monkeypatch.setattr(module, "_plausible_shape", lambda _path, _value: True)
    with pytest.raises(
        transition.PassiveTransitionRejected, match="original passive authority",
    ):
        transition.review_passive_readiness_transition(
            _snapshot(), _snapshot(),
        )


def test_predicate_replacement_between_child_reviews_is_rejected(monkeypatch):
    native = transition.review_unapproved_v3_snapshot_shapes
    count = []

    def after_first(mapping):
        result = native(mapping)
        if not count:
            count.append("first")
            monkeypatch.setattr(
                shape, "_plausible_shape", lambda _path, _value: True,
            )
        return result

    monkeypatch.setattr(
        transition, "review_unapproved_v3_snapshot_shapes", after_first,
    )
    with pytest.raises(
        transition.PassiveTransitionRejected, match="original passive authority",
    ):
        transition.review_passive_readiness_transition(
            _snapshot(), _snapshot(),
        )
    assert count == ["first"]


def test_unmodified_placeholder_review_remains_inert():
    report = transition.review_passive_readiness_transition(
        _snapshot(), _snapshot(),
    )
    assert report.before_sha256 == report.after_sha256
    assert report.newly_plausible_paths == ()
    assert report.external_compute_authorized is False
    assert report.real_training_authorized is False
    assert report.protected_v2_authorized is False
