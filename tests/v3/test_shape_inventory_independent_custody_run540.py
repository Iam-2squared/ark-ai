"""An unapproved V3 shape report must not trust a substituted inventory callback.

All snapshots are local placeholders; these checks never open training gates.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ark.learning import offline_snapshot_shape_review as shape
from ark.learning import offline_readiness_transition as transition

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def test_passive_unapproved_inventory_shape_alias_remains_consistent():
    snapshot = _snapshot()
    original = shape.review_unapproved_v3_snapshot_shapes(snapshot)
    assert original.checked_path_count == 26
    assert len(original.unresolved_paths) == 26
    assert "tokenizer.revision" in original.unresolved_paths
    snapshot["base"]["revision"] = "a" * 40
    changed = shape.review_unapproved_v3_snapshot_shapes(snapshot)
    assert "base.revision" not in changed.unresolved_paths
    assert "tokenizer.revision" not in changed.unresolved_paths
    assert changed.preflight_authorized is False


@pytest.mark.parametrize("forgery", (
    "omit", "duplicate", "reverse", "invented", "empty", "alias_removed",
))
def test_inventory_with_correct_hash_but_forged_paths_is_rejected(
    monkeypatch, forgery,
):
    snapshot = _snapshot()
    original = shape.inventory_unapproved_v3_readiness

    def forged_inventory(mapping):
        report = original(mapping)
        paths = list(report.unresolved_paths)
        if forgery == "omit":
            paths.pop()
        elif forgery == "duplicate":
            paths.append(paths[0])
        elif forgery == "reverse":
            paths.reverse()
        elif forgery == "invented":
            paths[0] = "authorization.real_training_authorized"
        elif forgery == "empty":
            paths = []
        else:
            paths.remove("tokenizer.revision")
        return replace(
            report, unresolved_paths=tuple(paths), unresolved_count=len(paths),
        )

    monkeypatch.setattr(
        shape, "inventory_unapproved_v3_readiness", forged_inventory,
    )
    with pytest.raises(shape.OfflineShapeRejected):
        shape.review_unapproved_v3_snapshot_shapes(snapshot)
    with pytest.raises(transition.PassiveTransitionRejected):
        transition.review_passive_readiness_transition(
            _snapshot(), _snapshot(),
        )


@pytest.mark.parametrize("authority", (
    "external_compute_authorized", "candidate_generation_authorized",
    "protected_evaluation_authorized", "promotion_authorized",
))
def test_inventory_callback_cannot_grant_authority_after_own_validation(
    monkeypatch, authority,
):
    native = shape.inventory_unapproved_v3_readiness

    def postcheck_rebind(mapping):
        report = native(mapping)
        monkeypatch.setattr(
            shape.OfflineReadinessInventory, authority,
            property(lambda self: True),
        )
        return report

    monkeypatch.setattr(
        shape, "inventory_unapproved_v3_readiness", postcheck_rebind,
    )
    with pytest.raises(shape.OfflineShapeRejected, match="authority"):
        shape.review_unapproved_v3_snapshot_shapes(_snapshot())


@pytest.mark.parametrize("mutation", ("new_paths", "equal_carrier", "new_count"))
def test_late_shape_callback_cannot_replace_inventory_receipt(
    monkeypatch, mutation,
):
    snapshot = _snapshot()
    snapshot["code"]["git_sha"] = "a" * 40
    source = shape.inventory_unapproved_v3_readiness
    native_plausible = shape._plausible_shape
    captured = []

    def collect(mapping):
        report = source(mapping)
        captured.append(report)
        return report

    def after_inventory(path, value):
        if path == "code.git_sha":
            report = captured[0]
            if mutation == "new_paths":
                object.__setattr__(report, "unresolved_paths", ())
            elif mutation == "equal_carrier":
                original = report.unresolved_paths
                clone = tuple(list(original))
                assert clone == original and clone is not original
                object.__setattr__(report, "unresolved_paths", clone)
            else:
                object.__setattr__(report, "unresolved_count", 0)
        return native_plausible(path, value)

    monkeypatch.setattr(shape, "inventory_unapproved_v3_readiness", collect)
    monkeypatch.setattr(shape, "_plausible_shape", after_inventory)
    with pytest.raises(shape.OfflineShapeRejected):
        shape.review_unapproved_v3_snapshot_shapes(snapshot)
