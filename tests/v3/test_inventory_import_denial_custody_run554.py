"""Passive V3 inventories must retain their original denied authority methods."""

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_inventory as inv

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "name",
    (
        "external_compute_authorized",
        "candidate_generation_authorized",
        "protected_evaluation_authorized",
        "promotion_authorized",
    ),
)
def test_preinstalled_false_only_denial_is_not_original(monkeypatch, name):
    invocations = []

    def forged(self):
        invocations.append(name)
        return False

    monkeypatch.setattr(inv.OfflineReadinessInventory, name, property(forged))
    with pytest.raises(
        inv.OfflineReadinessRejected,
        match="readiness authority descriptor changed",
    ):
        inv.inventory_unapproved_v3_readiness(_snapshot())
    # The forged getter must not be used as an accepted baseline.
    assert invocations == []


def test_preinstalled_true_denial_is_rejected_before_output(monkeypatch):
    monkeypatch.setattr(
        inv.OfflineReadinessInventory,
        "external_compute_authorized",
        property(lambda self: True),
    )
    with pytest.raises(
        inv.OfflineReadinessRejected, match="descriptor changed"
    ):
        inv.inventory_unapproved_v3_readiness(_snapshot())


def test_reentrant_replacement_during_hashing_is_rejected(monkeypatch):
    original = inv.hashlib.sha256

    def replace_denial(value):
        digest = original(value)
        monkeypatch.setattr(
            inv.OfflineReadinessInventory,
            "promotion_authorized",
            property(lambda self: False),
        )
        return digest

    monkeypatch.setattr(inv.hashlib, "sha256", replace_denial)
    with pytest.raises(
        inv.OfflineReadinessRejected, match="descriptor changed"
    ):
        inv.inventory_unapproved_v3_readiness(_snapshot())


def test_original_unapproved_inventory_is_still_non_authorizing():
    result = inv.inventory_unapproved_v3_readiness(_snapshot())
    assert result.unresolved_count == 26
    assert result.external_compute_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.protected_evaluation_authorized is False
    assert result.promotion_authorized is False
