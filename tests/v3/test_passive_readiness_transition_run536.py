"""Passive V3 snapshot progress never implies training or billing consent."""

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


def _denials(result):
    for name in transition._DENIED:
        assert getattr(result, name) is False


def test_identical_template_has_no_transition_or_permission():
    result = transition.review_passive_readiness_transition(
        _snapshot(), _snapshot(),
    )
    assert result.before_sha256 == result.after_sha256
    assert result.newly_plausible_paths == ()
    assert result.became_unresolved_paths == ()
    assert result.newly_malformed_paths == ()
    assert result.syntax_repaired_paths == ()
    _denials(result)


def test_alias_resolution_is_only_string_plausibility():
    before, after = _snapshot(), _snapshot()
    after["base"]["revision"] = "a" * 40
    after["code"]["git_sha"] = "b" * 40
    result = transition.review_passive_readiness_transition(before, after)
    assert result.newly_plausible_paths == (
        "base.revision", "code.git_sha", "tokenizer.revision",
    )
    assert result.newly_malformed_paths == ()
    assert result.before_sha256 != result.after_sha256
    _denials(result)


@pytest.mark.parametrize("path,value", (
    ("code.git_sha", "not-an-immutable-commit"),
    ("dataset.canonical_sha256", "A" * 64),
    ("budget.wall_clock_timeout_minutes", True),
    ("export.converter_identity", "sha-not-present"),
))
def test_bad_value_is_not_counted_as_resolved(path, value):
    before, after = _snapshot(), _snapshot()
    section, key = path.split(".")
    after[section][key] = value
    result = transition.review_passive_readiness_transition(before, after)
    assert path not in result.newly_plausible_paths
    assert path in result.newly_malformed_paths
    _denials(result)


def test_invalid_to_hash_shaped_transition_only_repairs_syntax():
    before, after = _snapshot(), _snapshot()
    before["export"]["converter_identity"] = "not-a-real-tool"
    after["export"]["converter_identity"] = "f" * 64
    result = transition.review_passive_readiness_transition(before, after)
    assert result.syntax_repaired_paths == ("export.converter_identity",)
    assert result.newly_plausible_paths == ()
    _denials(result)


def test_plausible_identity_back_to_placeholder_is_regression():
    before, after = _snapshot(), _snapshot()
    before["dataset"]["canonical_sha256"] = "b" * 64
    result = transition.review_passive_readiness_transition(before, after)
    assert result.became_unresolved_paths == ("dataset.canonical_sha256",)
    _denials(result)


def test_invalid_to_unresolved_is_not_syntax_repaired():
    before, after = _snapshot(), _snapshot()
    before["export"]["quantizer_identity"] = "missing"
    result = transition.review_passive_readiness_transition(before, after)
    assert result.syntax_repaired_paths == ()
    assert "export.quantizer_identity" in result.became_unresolved_paths


@pytest.mark.parametrize("flag,value", (
    ("external_compute_authorized", True),
    ("preflight_authorized", 1),
    ("candidate_generation_authorized", True),
    ("injected_authorization", False),
))
def test_any_new_authority_claim_refused(flag, value):
    before, after = _snapshot(), _snapshot()
    after["authorization"][flag] = value
    with pytest.raises(transition.PassiveTransitionRejected):
        transition.review_passive_readiness_transition(before, after)


def test_wrong_experiment_and_non_dict_refused():
    with pytest.raises(transition.PassiveTransitionRejected):
        transition.review_passive_readiness_transition([], _snapshot())
    after = _snapshot()
    after["experiment_id"] = "other"
    with pytest.raises(transition.PassiveTransitionRejected):
        transition.review_passive_readiness_transition(_snapshot(), after)


def test_insertion_order_does_not_change_passive_digest():
    before, after = _snapshot(), _snapshot()
    after["code"]["git_sha"] = "e" * 40
    first = transition.review_passive_readiness_transition(before, after)
    second = transition.review_passive_readiness_transition(
        dict(reversed(list(before.items()))),
        dict(reversed(list(after.items()))),
    )
    assert first == second


def test_reentrant_mutation_after_first_shape_check_refused(monkeypatch):
    before, after = _snapshot(), _snapshot()
    original = transition.review_unapproved_v3_snapshot_shapes
    called = [0]

    def mutating_shape(value):
        result = original(value)
        called[0] += 1
        if called[0] == 1:
            after["code"]["git_sha"] = "a" * 40
        return result

    monkeypatch.setattr(
        transition, "review_unapproved_v3_snapshot_shapes", mutating_shape,
    )
    with pytest.raises(transition.PassiveTransitionRejected):
        transition.review_passive_readiness_transition(before, after)


def test_false_permission_getter_cannot_rewrite_returned_witness(monkeypatch):
    before, after = _snapshot(), _snapshot()

    def mutate(self):
        object.__setattr__(self, "newly_plausible_paths", ())
        object.__setattr__(self, "after_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        transition.PassiveReadinessTransition, "promotion_authorized",
        property(mutate),
    )
    with pytest.raises(transition.PassiveTransitionRejected):
        transition.review_passive_readiness_transition(before, after)
