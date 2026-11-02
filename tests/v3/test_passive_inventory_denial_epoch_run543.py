"""Passive V3 inventory denial callbacks may not rewrite earlier authority."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import offline_readiness_inventory as inv

_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "earlier",
    ("external_compute_authorized", "candidate_generation_authorized",
     "protected_evaluation_authorized"),
)
@pytest.mark.parametrize("replacement", [False, True])
def test_last_false_getter_cannot_replace_prior_denial(
    monkeypatch, earlier, replacement,
):
    report_type = inv.OfflineReadinessInventory

    def mutate(self):
        monkeypatch.setattr(
            report_type, earlier,
            property(lambda ignored: replacement),
        )
        return False

    monkeypatch.setattr(
        report_type, "promotion_authorized", property(mutate),
    )
    with pytest.raises(
        inv.OfflineReadinessRejected,
        match="readiness authority descriptor changed",
    ):
        inv.inventory_unapproved_v3_readiness(_snapshot())


def test_preinstalled_mutating_getter_rejected_before_inventory(monkeypatch):
    report_type = inv.OfflineReadinessInventory
    calls = []

    def mutate(self):
        calls.append(1)
        object.__setattr__(
            self, "unresolved_paths", tuple(list(self.unresolved_paths)),
        )
        return False

    monkeypatch.setattr(
        report_type, "promotion_authorized", property(mutate),
    )
    # The earlier failure was a later output-carrier rebind. Original
    # descriptor custody now refuses this preinstalled callback *before* it
    # runs, without accepting any substituted False-returning implementation.
    with pytest.raises(
        inv.OfflineReadinessRejected,
        match="readiness authority descriptor changed",
    ):
        inv.inventory_unapproved_v3_readiness(_snapshot())
    assert calls == []


def test_passive_inventory_remains_unapproved_without_callbacks():
    report = inv.inventory_unapproved_v3_readiness(_snapshot())
    assert report.unresolved_count == 26
    assert report.external_compute_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
    assert report.promotion_authorized is False
