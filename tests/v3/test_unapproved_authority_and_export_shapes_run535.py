"""Passive V3 review rejects hidden authority and fake export identities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_inventory as inventory
from ark.learning import offline_snapshot_shape_review as shapes

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("key,value", (
    ("candidate_generation_authorized", True),
    ("protected_evaluation_authorized", True),
    ("paid_compute_authorized", True),
    ("injected", False),
    ("external_compute_authorized_extra", None),
))
def test_extra_authority_claim_fails_closed_before_passive_inventory(key, value):
    snapshot = _snapshot()
    snapshot["authorization"][key] = value
    with pytest.raises(inventory.OfflineReadinessRejected, match="unapproved"):
        inventory.inventory_unapproved_v3_readiness(snapshot)
    with pytest.raises(shapes.OfflineShapeRejected):
        shapes.review_unapproved_v3_snapshot_shapes(snapshot)


@pytest.mark.parametrize("field,value", (
    ("converter_identity", "synthetic-nonhash"),
    ("converter_identity", "A" * 64),
    ("converter_identity", "0" * 63),
    ("quantizer_identity", 1),
    ("quantizer_identity", "f" * 65),
))
def test_export_tool_identity_must_have_sha256_syntax(field, value):
    snapshot = _snapshot()
    snapshot["export"][field] = value
    report = shapes.review_unapproved_v3_snapshot_shapes(snapshot)
    path = f"export.{field}"
    assert path in report.invalid_shape_paths
    assert path not in report.unresolved_paths
    assert report.external_compute_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.v2_opening_authorized is False


@pytest.mark.parametrize("field", ("converter_identity", "quantizer_identity"))
def test_hash_shaped_export_identity_is_not_a_verified_artifact(field):
    snapshot = _snapshot()
    snapshot["export"][field] = "b" * 64
    report = shapes.review_unapproved_v3_snapshot_shapes(snapshot)
    assert f"export.{field}" not in report.invalid_shape_paths
    assert f"export.{field}" not in report.unresolved_paths
    assert report.real_training_authorized is False
    assert report.promotion_authorized is False


def test_literal_unresolved_export_identity_is_not_misclassified_as_bad_hash():
    snapshot = _snapshot()
    report = shapes.review_unapproved_v3_snapshot_shapes(snapshot)
    assert "export.converter_identity" in report.unresolved_paths
    assert "export.quantizer_identity" in report.unresolved_paths
    assert "export.converter_identity" not in report.invalid_shape_paths
    assert "export.quantizer_identity" not in report.invalid_shape_paths
