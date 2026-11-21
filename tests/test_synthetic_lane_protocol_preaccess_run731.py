"""A disconnected lane recommendation must not invoke forged private-path helpers.

All lanes are synthetic; selection never authorizes GitHub writes or spending.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

import ark.agency_synthetic_lane_selector_review as mod


def _lanes():
    return (
        mod.SyntheticWorkLane(
            "memory", 20, ("src/ark/memory",), (),
            (), "free_local", False, True,
        ),
        mod.SyntheticWorkLane(
            "planner", 10, ("src/ark/agency/planner.py",), (),
            (), "free_local", False, True,
        ),
    )


@pytest.mark.parametrize("surface", (
    "hash_module", "hash_callback", "json_module", "json_callback",
    "label_pattern", "path_pattern", "costs", "domain", "limit",
    "fields_helper", "overlap_helper", "lane_field", "lane_ctor",
    "result_field", "result_ctor", "denial",
))
def test_recommendation_dependency_drift_denied_before_private_path_read(
    monkeypatch, surface,
):
    lanes = _lanes()
    invoked = []

    def hostile(*_args, **_kwargs):
        invoked.append(surface)
        raise AssertionError("hostile path/identity handler was executed")

    with monkeypatch.context() as patch:
        if surface == "hash_module":
            patch.setattr(mod, "hashlib", SimpleNamespace(sha256=hostile))
        elif surface == "hash_callback":
            patch.setattr(mod.hashlib, "sha256", hostile)
        elif surface == "json_module":
            patch.setattr(mod, "json", SimpleNamespace(dumps=hostile))
        elif surface == "json_callback":
            patch.setattr(mod.json, "dumps", hostile)
        elif surface == "label_pattern":
            patch.setattr(mod, "_LABEL", re.compile(".*"))
        elif surface == "path_pattern":
            patch.setattr(mod, "_PATH_COMPONENT", re.compile(".*"))
        elif surface == "costs":
            patch.setattr(mod, "_COSTS", frozenset(("free_local",)))
        elif surface == "domain":
            patch.setattr(mod, "_DOMAIN", bytes(bytearray(mod._DOMAIN)))
        elif surface == "limit":
            patch.setattr(mod, "_MAX_SELECTED", mod._MAX_SELECTED + 1)
        elif surface == "fields_helper":
            patch.setattr(mod, "fields", hostile)
        elif surface == "overlap_helper":
            patch.setattr(mod, "_overlap", hostile)
        elif surface == "lane_field":
            patch.setattr(mod.SyntheticWorkLane, "touches", property(hostile))
        elif surface == "lane_ctor":
            patch.setattr(mod.SyntheticWorkLane, "__init__", hostile)
        elif surface == "result_field":
            patch.setattr(
                mod.SyntheticLaneSelection, "selected", property(hostile),
            )
        elif surface == "result_ctor":
            patch.setattr(mod.SyntheticLaneSelection, "__init__", hostile)
        else:
            patch.setattr(
                mod.SyntheticLaneSelection, "execution_authorized",
                property(hostile),
            )
        with pytest.raises(
            mod.SyntheticLaneSelectionRejected,
            match="parser, codec or denial authority changed",
        ):
            mod.review_disconnected_work_lanes(lanes)
    assert invoked == []
    assert lanes[0].lane_id == "memory"
    assert lanes[1].touches == ("src/ark/agency/planner.py",)


def test_original_disconnected_selector_still_avoids_ci_overlap():
    result = mod.review_disconnected_work_lanes(
        _lanes(), inflight_paths=("src/ark/agency",),
    )
    assert result.selected == ("memory",)
    assert result.deferred == (("planner", "inflight_ci_conflict"),)
    assert result.execution_authorized is False
    assert result.github_write_authorized is False
    assert result.spending_authorized is False
