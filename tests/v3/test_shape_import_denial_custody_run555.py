"""Passive V3 shape diagnostics preserve original denial-only class properties.

All inputs are unapproved template fixtures; this suite does not run a model,
grant preflight/training permission, or authenticate file/human identities.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_snapshot_shape_review as shape

TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("flag", shape._DENIED)
def test_preinstalled_false_shape_denial_is_not_a_trusted_original(
    monkeypatch, flag,
):
    entered = []

    def substituted(self):
        entered.append(flag)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            shape.UnapprovedSnapshotShapeReview, flag, property(substituted),
        )
        with pytest.raises(shape.OfflineShapeRejected, match="result changed"):
            shape.review_unapproved_v3_snapshot_shapes(_snapshot())
    assert entered == []


@pytest.mark.parametrize("flag", shape._INVENTORY_DENIALS)
def test_preinstalled_false_inventory_denial_cannot_be_laundered(
    monkeypatch, flag,
):
    entered = []

    def substituted(self):
        entered.append(flag)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(shape.OfflineReadinessInventory, flag, property(substituted))
        with pytest.raises(shape.OfflineShapeRejected):
            shape.review_unapproved_v3_snapshot_shapes(_snapshot())
    assert entered == []


def test_late_false_shape_denial_substitution_is_rejected(
    monkeypatch,
):
    snapshot = _snapshot()
    snapshot["code"]["git_sha"] = "a" * 40
    native = shape._plausible_shape
    touched = []

    def substitute(path, value):
        if path == "code.git_sha":
            monkeypatch.setattr(
                shape.UnapprovedSnapshotShapeReview,
                "preflight_authorized",
                property(lambda self: touched.append(True) or False),
            )
        return native(path, value)

    with monkeypatch.context() as patch:
        patch.setattr(shape, "_plausible_shape", substitute)
        with pytest.raises(shape.OfflineShapeRejected, match="result changed"):
            shape.review_unapproved_v3_snapshot_shapes(snapshot)
    assert touched == []


def test_clean_unapproved_shape_remains_non_authorizing():
    result = shape.review_unapproved_v3_snapshot_shapes(_snapshot())
    assert result.checked_path_count == 26
    assert len(result.unresolved_paths) == 26
    assert all(getattr(result, flag) is False for flag in shape._DENIED)
