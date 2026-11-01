"""Passive V3 diagnostics must not trust retargeted source review callbacks.

No model, GPU, Candidate, protected evaluation or execution authorization.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ark.learning import offline_readiness_transition as transition

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("target", ("sha", "paths"))
def test_equal_value_output_carrier_replacement_is_not_a_stable_epoch(
    monkeypatch, target,
):
    before, after = _snapshot(), _snapshot()
    after["code"]["git_sha"] = "a" * 40

    def retarget(self):
        if target == "sha":
            old = self.before_sha256
            replacement = ("#" + old)[1:]
            assert replacement == old and replacement is not old
            object.__setattr__(self, "before_sha256", replacement)
        else:
            old = self.newly_plausible_paths
            replacement = tuple(list(old))
            assert replacement == old and replacement is not old
            object.__setattr__(self, "newly_plausible_paths", replacement)
        return False

    monkeypatch.setattr(
        transition.PassiveReadinessTransition,
        "human_approval_verified",
        property(retarget),
    )
    with pytest.raises(transition.PassiveTransitionRejected, match="report changed"):
        transition.review_passive_readiness_transition(before, after)


def test_exact_shape_result_with_forged_sha_cannot_relabel_snapshot(monkeypatch):
    native = transition.review_unapproved_v3_snapshot_shapes

    def fake_sha(mapping):
        return replace(native(mapping), snapshot_sha256="f" * 64)

    monkeypatch.setattr(
        transition, "review_unapproved_v3_snapshot_shapes", fake_sha,
    )
    with pytest.raises(transition.PassiveTransitionRejected, match="digest mismatch"):
        transition.review_passive_readiness_transition(_snapshot(), _snapshot())


@pytest.mark.parametrize("target", ("source_paths", "equal_clone"))
def test_final_denial_getter_cannot_retarget_initial_source_report(
    monkeypatch, target,
):
    observed = []
    native = transition.review_unapproved_v3_snapshot_shapes

    def capture(mapping):
        result = native(mapping)
        observed.append(result)
        return result

    def retarget(_self):
        assert len(observed) == 2
        first = observed[0]
        if target == "source_paths":
            object.__setattr__(first, "unresolved_paths", ("fake.field",))
        else:
            original = first.unresolved_paths
            clone = tuple(list(original))
            assert clone == original and clone is not original
            object.__setattr__(first, "unresolved_paths", clone)
        return False

    monkeypatch.setattr(
        transition, "review_unapproved_v3_snapshot_shapes", capture,
    )
    monkeypatch.setattr(
        transition.PassiveReadinessTransition,
        "human_approval_verified", property(retarget),
    )
    with pytest.raises(transition.PassiveTransitionRejected, match="source report changed"):
        transition.review_passive_readiness_transition(_snapshot(), _snapshot())


def test_same_unapproved_snapshots_still_produce_zero_authority():
    result = transition.review_passive_readiness_transition(
        _snapshot(), _snapshot(),
    )
    assert result.before_sha256 == result.after_sha256
    assert result.newly_plausible_paths == ()
    assert result.artifact_identity_verified is False
    assert result.human_approval_verified is False
    assert result.real_training_authorized is False
