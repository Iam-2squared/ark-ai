"""Free-only V3 syntax review: exact alias and positive cost, never approval.

No GPU, provider calls, model weights, candidate, V2 evaluation or write.
"""

import json
from pathlib import Path

from ark.learning.offline_readiness_inventory import inventory_unapproved_v3_readiness
from ark.learning.offline_readiness_transition import review_passive_readiness_transition
from ark.learning.offline_snapshot_shape_review import review_unapproved_v3_snapshot_shapes

_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


def test_zero_cost_is_malformed_not_preflight_ready():
    snapshot = _snapshot()
    snapshot["budget"]["max_cost_jpy"] = 0
    report = review_unapproved_v3_snapshot_shapes(snapshot)
    assert "budget.max_cost_jpy" in report.invalid_shape_paths
    assert "budget.max_cost_jpy" not in report.unresolved_paths
    assert report.external_compute_authorized is False
    assert report.preflight_authorized is False


def test_zero_cost_transition_does_not_count_as_newly_plausible():
    before = _snapshot()
    after = _snapshot()
    after["budget"]["max_cost_jpy"] = 0
    report = review_passive_readiness_transition(before, after)
    assert "budget.max_cost_jpy" in report.newly_malformed_paths
    assert "budget.max_cost_jpy" not in report.newly_plausible_paths
    assert report.external_compute_authorized is False
    assert report.human_approval_verified is False


def test_positive_synthetic_cost_is_only_a_syntax_hint():
    snapshot = _snapshot()
    snapshot["budget"]["max_cost_jpy"] = 1
    report = review_unapproved_v3_snapshot_shapes(snapshot)
    assert "budget.max_cost_jpy" not in report.invalid_shape_paths
    assert "budget.max_cost_jpy" not in report.unresolved_paths
    assert report.real_training_authorized is False
    assert report.promotion_authorized is False


def test_equal_string_subclass_alias_is_not_an_unresolved_literal():
    class ForgedAlias(str):
        pass

    snapshot = _snapshot()
    snapshot["tokenizer"]["revision"] = ForgedAlias("SAME_AS_BASE")
    inventory = inventory_unapproved_v3_readiness(snapshot)
    report = review_unapproved_v3_snapshot_shapes(snapshot)
    assert "tokenizer.revision" not in inventory.unresolved_paths
    assert "tokenizer.revision" not in report.unresolved_paths
    assert "tokenizer.revision" in report.invalid_shape_paths
    assert report.candidate_generation_authorized is False


def test_forged_alias_transition_remains_malformed_and_non_authorizing():
    class ForgedAlias(str):
        pass

    before = _snapshot()
    after = _snapshot()
    after["tokenizer"]["revision"] = ForgedAlias("SAME_AS_BASE")
    report = review_passive_readiness_transition(before, after)
    assert "tokenizer.revision" in report.newly_malformed_paths
    assert "tokenizer.revision" not in report.newly_plausible_paths
    assert report.artifact_identity_verified is False
    assert report.protected_v2_authorized is False


def test_exact_literal_alias_retains_unresolved_base_dependency():
    before = _snapshot()
    report = review_unapproved_v3_snapshot_shapes(before)
    assert "tokenizer.revision" in report.unresolved_paths
    after = _snapshot()
    after["base"]["revision"] = "a" * 40
    transition = review_passive_readiness_transition(before, after)
    assert "tokenizer.revision" in transition.newly_plausible_paths
    assert transition.human_approval_verified is False
