"""Exact-type gate admission after synthetic frozen-object reflection.

No real dispatch, durable authorization, user grant or external clock occurs.
"""

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate


def _fixture():
    return (
        PermissionGate(),
        ToolSpec("fixture", "local.write", Effect.WRITE),
        ToolCall("fixture", "local.write", "sandbox", {"n": 1}),
        [CapabilityGrant("local.write", "sandbox")],
    )


@pytest.mark.parametrize("wrong_effect", ["write", None, True, 1])
def test_reflected_non_effect_is_not_treated_as_read(wrong_effect):
    gate, spec, call, grants = _fixture()
    object.__setattr__(spec, "effect", wrong_effect)
    touched = []

    def grants_with_side_effect():
        touched.append("ITERATED")
        yield from grants

    with pytest.raises(PermissionDenied, match="exact tool identity and effect"):
        gate.authorize(spec, call, grants_with_side_effect(), now_ms=100)
    assert touched == []


class HostileEquality:
    def __eq__(self, other):
        raise AssertionError("hostile equality was called")


@pytest.mark.parametrize(("target", "field"), [
    ("spec", "name"),
    ("spec", "capability"),
    ("call", "tool"),
    ("call", "scope"),
])
def test_reflected_foreign_label_refused_before_comparison(target, field):
    gate, spec, call, grants = _fixture()
    object.__setattr__(spec if target == "spec" else call, field, HostileEquality())
    with pytest.raises(PermissionDenied, match="exact tool identity and effect"):
        gate.authorize(spec, call, grants, now_ms=100)


def test_valid_read_grant_still_admitted_without_one_shot():
    gate = PermissionGate()
    spec = ToolSpec("fixture", "local.read", Effect.READ)
    call = ToolCall("fixture", "local.read", "sandbox", {"value": 1})
    gate.authorize(
        spec, call, [CapabilityGrant("local.read", "sandbox")], now_ms=100,
    )


def test_valid_write_still_requires_one_shot():
    gate, spec, call, grants = _fixture()
    with pytest.raises(PermissionDenied, match="one-shot"):
        gate.authorize(spec, call, grants, now_ms=100)
