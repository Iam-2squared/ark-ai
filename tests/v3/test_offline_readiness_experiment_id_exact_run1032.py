"""Run1032: passive V3 inventory requires exact experiment identity text."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_inventory as inv

_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


class ForgivingText(str):
    """A hostile string subclass that lies during equality checks."""

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = str.__hash__


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


def test_experiment_id_string_subclass_cannot_fake_frozen_identity():
    snapshot = _snapshot()
    snapshot["experiment_id"] = ForgivingText("not-the-frozen-experiment")
    with pytest.raises(
        inv.OfflineReadinessRejected,
        match="frozen experiment identity required",
    ):
        inv.inventory_unapproved_v3_readiness(snapshot)


def test_exact_builtin_experiment_id_keeps_passive_inventory_behavior():
    result = inv.inventory_unapproved_v3_readiness(_snapshot())
    assert result.unresolved_count == 26
    assert result.external_compute_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.protected_evaluation_authorized is False
    assert result.promotion_authorized is False
