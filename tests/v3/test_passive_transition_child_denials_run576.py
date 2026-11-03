"""Import-pinned V3 shape denial properties must survive passive transition.

Tests use only synthetic dictionary snapshots; no execution, preflight,
Candidate, external service, protected V2 evaluation or billing action.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as mod

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


@pytest.mark.parametrize("name", mod._SOURCE_DENIALS)
def test_false_only_child_descriptor_replacement_denied_before_snapshots(
    monkeypatch, name,
):
    touched = []

    def forbidden(_value):
        touched.append(True)
        raise AssertionError("snapshot should not be inspected")

    monkeypatch.setattr(mod, "_pin_json_tree", forbidden)
    monkeypatch.setattr(mod.UnapprovedSnapshotShapeReview, name, property(
        lambda _: False,
    ))
    with pytest.raises(mod.PassiveTransitionRejected, match="original passive"):
        mod.review_passive_readiness_transition({}, {})
    assert touched == []


def test_original_child_denials_keep_unapproved_review_non_authorizing():
    snapshot = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    result = mod.review_passive_readiness_transition(snapshot, snapshot)
    assert result.before_sha256 == result.after_sha256
    assert result.newly_plausible_paths == ()
    assert result.candidate_generation_authorized is False
    assert result.protected_v2_authorized is False
    assert result.external_compute_authorized is False
