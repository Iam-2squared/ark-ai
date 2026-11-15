"""PlanGraph rejects reflected mapping carriers before request hashing.

A normal ToolCall freezes JSON to a MappingProxyType. An injected foreign
Mapping may have executable enumeration hooks; no such hook may run while
checking a synthetic PlanGraph. This grants no permission to execute steps.
"""

from collections.abc import Mapping

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph


class _MappingTrap(Mapping):
    def __init__(self):
        self.calls = 0

    def __iter__(self):
        self.calls += 1
        raise AssertionError("foreign mapping iterator must not run")

    def __len__(self):
        self.calls += 1
        raise AssertionError("foreign mapping length must not run")

    def __getitem__(self, _key):
        self.calls += 1
        raise AssertionError("foreign mapping item access must not run")


def _call():
    return ToolCall(
        "offline.inspect", "fixture.read", "synthetic",
        {"items": [{"a": 1}, {"b": 2}]},
    )


def test_foreign_argument_mapping_is_denied_without_enumeration():
    call = _call()
    trap = _MappingTrap()
    object.__setattr__(call, "arguments", trap)
    with pytest.raises(PlanConflictError, match="carrier changed"):
        PlanGraph((PlanStep("synthetic-step", call),))
    assert trap.calls == 0


@pytest.mark.parametrize("replacement", ({}, {"items": [{"a": 1}, {"b": 2}]}))
def test_reflected_plain_dict_cannot_replace_frozen_argument_carrier(replacement):
    call = _call()
    object.__setattr__(call, "arguments", replacement)
    with pytest.raises(PlanConflictError, match="carrier changed"):
        PlanGraph((PlanStep("synthetic-step", call),))


def test_unmodified_nested_json_arguments_remain_admitted_without_execution():
    graph = PlanGraph((PlanStep("synthetic-step", _call()),))
    assert graph.topology_digest().startswith("plan_")
    assert len(graph.statuses()) == 1
