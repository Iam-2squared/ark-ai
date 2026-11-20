"""Run1024: pin the passive V3 readiness inventory protocol before inspection.

All snapshots are synthetic JSON fixtures. These checks never authorize compute,
Candidate generation, protected evaluation, export, or promotion.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pytest

from ark.learning import offline_readiness_inventory as inv

_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    return json.loads(_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "vector",
    ("_SECTIONS", "_PLACEHOLDERS", "_DENIED", "_AUTHORITY"),
)
def test_rebound_inventory_field_vectors_are_rejected(vector, monkeypatch):
    original = getattr(inv, vector)
    if vector == "_SECTIONS":
        replacement = MappingProxyType(dict(original))
    elif vector == "_PLACEHOLDERS":
        replacement = frozenset(set(original))
    else:
        replacement = tuple(list(original))
    assert replacement == original
    assert replacement is not original

    with monkeypatch.context() as patch:
        patch.setattr(inv, vector, replacement)
        with pytest.raises(
            inv.OfflineReadinessRejected, match="protocol changed",
        ):
            inv.inventory_unapproved_v3_readiness(_snapshot())


def test_section_inventory_cannot_be_mutated_in_place():
    with pytest.raises(TypeError):
        inv._SECTIONS["code"] = ("manifest_sha256",)


@pytest.mark.parametrize("dependency", ("sha256", "dumps", "pin", "epoch"))
def test_rebound_digest_or_snapshot_dependency_is_rejected_before_callback(
    dependency, monkeypatch,
):
    called = []

    def forbidden(*_args, **_kwargs):
        called.append(dependency)
        raise AssertionError("substituted inventory dependency executed")

    with monkeypatch.context() as patch:
        if dependency == "sha256":
            patch.setattr(inv.hashlib, "sha256", forbidden)
        elif dependency == "dumps":
            patch.setattr(inv.json, "dumps", forbidden)
        elif dependency == "pin":
            patch.setattr(inv, "_pin_json_tree", forbidden)
        else:
            patch.setattr(inv, "_assert_json_tree_epoch", forbidden)
        with pytest.raises(
            inv.OfflineReadinessRejected, match="protocol changed",
        ):
            inv.inventory_unapproved_v3_readiness(_snapshot())

    assert called == []


def test_replaced_false_authority_descriptor_is_rejected_without_getter_call(
    monkeypatch,
):
    called = []

    def forbidden(_self):
        called.append(True)
        raise AssertionError("substituted authority getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            inv.OfflineReadinessInventory,
            "promotion_authorized",
            property(forbidden),
        )
        with pytest.raises(
            inv.OfflineReadinessRejected, match="protocol changed",
        ):
            inv.inventory_unapproved_v3_readiness(_snapshot())

    assert called == []


def test_original_inventory_remains_passive_and_reports_all_placeholders():
    result = inv.inventory_unapproved_v3_readiness(_snapshot())
    assert result.unresolved_count == 26
    assert result.unresolved_paths == tuple(sorted(result.unresolved_paths))
    assert result.external_compute_authorized is False
    assert result.candidate_generation_authorized is False
    assert result.protected_evaluation_authorized is False
    assert result.promotion_authorized is False
