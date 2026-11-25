"""Unapproved V3 placeholder inventory remains a passive offline report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_inventory as inv

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def test_frozen_template_reports_only_literal_unresolved_positions():
    result = inv.inventory_unapproved_v3_readiness(_snapshot())
    assert result.unresolved_count == 26
    assert result.unresolved_paths == tuple(sorted(result.unresolved_paths))
    assert "code.git_sha" in result.unresolved_paths
    assert "base.revision" in result.unresolved_paths
    assert "tokenizer.revision" in result.unresolved_paths
    assert "dataset.contamination_report_sha256" in result.unresolved_paths
    assert "budget.max_cost_jpy" in result.unresolved_paths
    assert "hardware.preflight_report_sha256" in result.unresolved_paths
    assert "method.rank" not in result.unresolved_paths
    assert result.external_compute_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.protected_evaluation_authorized is False
    assert result.promotion_authorized is False


def test_fake_resolved_value_reduces_placeholder_count_but_grants_no_authority():
    snapshot = _snapshot()
    snapshot["base"]["revision"] = "0" * 40
    snapshot["code"]["git_sha"] = "1" * 40
    result = inv.inventory_unapproved_v3_readiness(snapshot)
    assert result.unresolved_count == 23
    assert "base.revision" not in result.unresolved_paths
    assert "tokenizer.revision" not in result.unresolved_paths
    assert "code.git_sha" not in result.unresolved_paths
    assert result.external_compute_authorized is False


def test_no_placeholders_is_not_authenticated_readiness():
    snapshot = _snapshot()
    for section, keys in inv._SECTIONS.items():
        for key in keys:
            if snapshot[section][key] in ("UNRESOLVED", "USER_APPROVAL_REQUIRED"):
                snapshot[section][key] = "synthetic-only"
    snapshot["base"]["revision"] = "0" * 40
    result = inv.inventory_unapproved_v3_readiness(snapshot)
    assert result.unresolved_paths == ()
    assert result.unresolved_count == 0
    assert result.candidate_generation_authorized is False


@pytest.mark.parametrize("value", (True, 1, "false", None))
def test_unapproved_authority_requires_exact_false(value):
    snapshot = _snapshot()
    snapshot["authorization"]["external_compute_authorized"] = value
    with pytest.raises(inv.OfflineReadinessRejected, match="unapproved"):
        inv.inventory_unapproved_v3_readiness(snapshot)


@pytest.mark.parametrize("field", (
    "preflight_authorized", "real_training_authorized",
    "v2_opening_authorized", "promotion_authorized",
))
def test_other_authority_flags_are_not_ignored(field):
    snapshot = _snapshot()
    snapshot["authorization"][field] = True
    with pytest.raises(inv.OfflineReadinessRejected, match="unapproved"):
        inv.inventory_unapproved_v3_readiness(snapshot)


@pytest.mark.parametrize("mutation", ("missing", "wrong_type", "wrong_experiment"))
def test_structural_misrepresentation_fails_closed(mutation):
    snapshot = _snapshot()
    if mutation == "missing":
        del snapshot["environment"]["torch"]
    elif mutation == "wrong_type":
        snapshot["hardware"] = []
    else:
        snapshot["experiment_id"] = "not-the-frozen-experiment"
    with pytest.raises(inv.OfflineReadinessRejected):
        inv.inventory_unapproved_v3_readiness(snapshot)


def test_canonical_digest_independent_of_mapping_insertion_order():
    source = _snapshot()
    reordered = dict(reversed(list(source.items())))
    first = inv.inventory_unapproved_v3_readiness(source)
    second = inv.inventory_unapproved_v3_readiness(reordered)
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.unresolved_paths == second.unresolved_paths


def test_mutation_in_json_callback_rejected(monkeypatch):
    snapshot = _snapshot()
    original = inv.json.dumps

    def mutate(value, **kwargs):
        raw = original(value, **kwargs)
        snapshot["budget"]["max_cost_jpy"] = "changed-after-hash"
        return raw

    monkeypatch.setattr(inv.json, "dumps", mutate)
    with pytest.raises((inv.OfflineReadinessRejected, ValueError)):
        inv.inventory_unapproved_v3_readiness(snapshot)


def test_false_authority_getter_cannot_rewrite_result(monkeypatch):
    original = inv.OfflineReadinessInventory.promotion_authorized

    def side_effect(self):
        object.__setattr__(self, "unresolved_count", 0)
        return False

    monkeypatch.setattr(
        inv.OfflineReadinessInventory,
        "promotion_authorized",
        property(side_effect),
    )
    with pytest.raises(inv.OfflineReadinessRejected, match="changed"):
        inv.inventory_unapproved_v3_readiness(_snapshot())
    monkeypatch.setattr(inv.OfflineReadinessInventory, "promotion_authorized", original)
