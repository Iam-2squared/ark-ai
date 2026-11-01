"""V3 unapproved syntax review never converts placeholders into permission."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_snapshot_shape_review as review

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def test_unapproved_template_is_unresolved_not_invalid_or_authorized():
    result = review.review_unapproved_v3_snapshot_shapes(_snapshot())
    assert result.checked_path_count == 26
    assert len(result.unresolved_paths) == 26
    assert result.invalid_shape_paths == ()
    assert "tokenizer.revision" in result.unresolved_paths
    assert result.external_compute_authorized is False
    assert result.preflight_authorized is False
    assert result.real_training_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.v2_opening_authorized is False
    assert result.promotion_authorized is False


def test_fake_syntactic_resolution_is_reported_not_authenticated():
    snapshot = _snapshot()
    for section, keys in review._SECTIONS.items():
        for name in keys:
            if snapshot[section][name] in review._PLACEHOLDERS:
                snapshot[section][name] = "synthetic-not-an-identity"
    snapshot["base"]["revision"] = "synthetic-not-an-identity"
    result = review.review_unapproved_v3_snapshot_shapes(snapshot)
    assert result.unresolved_paths == ()
    assert "code.git_sha" in result.invalid_shape_paths
    assert "dataset.canonical_sha256" in result.invalid_shape_paths
    assert "tokenizer.revision" in result.invalid_shape_paths
    assert result.external_compute_authorized is False


def test_base_approval_placeholder_propagates_to_tokenizer_alias():
    snapshot = _snapshot()
    snapshot["base"]["revision"] = "USER_APPROVAL_REQUIRED"
    result = review.review_unapproved_v3_snapshot_shapes(snapshot)
    assert "base.revision" in result.unresolved_paths
    assert "tokenizer.revision" in result.unresolved_paths
    assert "tokenizer.revision" not in result.invalid_shape_paths


def test_plausible_hashes_are_only_strings_not_verified_bytes():
    snapshot = _snapshot()
    snapshot["base"]["revision"] = "a" * 40
    snapshot["code"]["git_sha"] = "b" * 40
    snapshot["dataset"]["canonical_sha256"] = "c" * 64
    result = review.review_unapproved_v3_snapshot_shapes(snapshot)
    assert "base.revision" not in result.unresolved_paths
    assert "tokenizer.revision" not in result.unresolved_paths
    assert "dataset.canonical_sha256" not in result.unresolved_paths
    assert result.invalid_shape_paths == ()
    assert result.candidate_generation_authorized is False


@pytest.mark.parametrize("path,value", (
    ("code.git_sha", "a" * 39),
    ("code.git_sha", "A" * 40),
    ("base.revision", 1234),
    ("dataset.provenance_manifest_sha256", "0" * 63),
    ("hardware.preflight_report_sha256", True),
    ("budget.max_cost_jpy", True),
    ("budget.wall_clock_timeout_minutes", 0),
    ("budget.wall_clock_timeout_minutes", 60.0),
    ("hardware.vram_gib", -1),
))
def test_malformed_nonplaceholder_values_report_exact_path(path, value):
    snapshot = _snapshot()
    section, field = path.split(".")
    snapshot[section][field] = value
    result = review.review_unapproved_v3_snapshot_shapes(snapshot)
    assert path in result.invalid_shape_paths
    assert path not in result.unresolved_paths


@pytest.mark.parametrize("alias", (True, 17, "BAD", "F" * 40))
def test_tokenizer_alias_must_be_exact_revision_or_bound_to_base(alias):
    snapshot = _snapshot()
    snapshot["base"]["revision"] = "a" * 40
    snapshot["tokenizer"]["revision"] = alias
    result = review.review_unapproved_v3_snapshot_shapes(snapshot)
    assert "tokenizer.revision" in result.invalid_shape_paths


@pytest.mark.parametrize("flag", (
    "external_compute_authorized", "preflight_authorized",
    "real_training_authorized", "v2_opening_authorized",
    "promotion_authorized",
))
def test_real_authority_input_refused_even_if_other_data_synthetic(flag):
    snapshot = _snapshot()
    snapshot["authorization"][flag] = True
    with pytest.raises(review.OfflineShapeRejected):
        review.review_unapproved_v3_snapshot_shapes(snapshot)


def test_identity_digest_ignores_mapping_insertion_order():
    source = _snapshot()
    reordered = dict(reversed(list(source.items())))
    first = review.review_unapproved_v3_snapshot_shapes(source)
    second = review.review_unapproved_v3_snapshot_shapes(reordered)
    assert first == second


def test_reflective_input_drift_during_shape_probe_is_rejected(monkeypatch):
    source = _snapshot()
    original = review._plausible_shape

    def mutate(path, value):
        if path == "code.git_sha":
            source["dataset"]["train_count"] = 121
        return original(path, value)

    monkeypatch.setattr(review, "_plausible_shape", mutate)
    with pytest.raises(review.OfflineShapeRejected):
        review.review_unapproved_v3_snapshot_shapes(source)


def test_false_property_cannot_rewrite_result(monkeypatch):
    original = review.UnapprovedSnapshotShapeReview.promotion_authorized

    def mutate(self):
        object.__setattr__(self, "invalid_shape_paths", ())
        return False

    monkeypatch.setattr(
        review.UnapprovedSnapshotShapeReview,
        "promotion_authorized", property(mutate),
    )
    snapshot = _snapshot()
    snapshot["code"]["git_sha"] = "synthetic-not-a-hash"
    with pytest.raises(review.OfflineShapeRejected, match="result changed"):
        review.review_unapproved_v3_snapshot_shapes(snapshot)
    monkeypatch.setattr(
        review.UnapprovedSnapshotShapeReview, "promotion_authorized", original,
    )
