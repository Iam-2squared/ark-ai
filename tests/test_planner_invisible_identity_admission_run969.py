"""Run969: optional PlanGraph refuses invisible IDs before creating a DAG.

All calls are inert; no registry execution, permission grant or tool dispatch.
Frozen PlanStep and ToolCall constructors remain unchanged.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph

_INVISIBLE_SCALARS = (
    0x00AD, 0x034F, 0x180E, 0x200B, 0x200C, 0x200D,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF,
    0x206A, 0x206B, 0x206C, 0x206D, 0x206E, 0x206F,
)


@pytest.mark.parametrize("codepoint", _INVISIBLE_SCALARS)
@pytest.mark.parametrize(
    "field", ("step_id", "depends_on", "tool", "capability", "scope"),
)
def test_invisible_identity_is_denied_before_plan_allocation(codepoint, field):
    hidden = "safe" + chr(codepoint) + "label"
    tool = hidden if field == "tool" else "mock.read"
    capability = hidden if field == "capability" else "read"
    scope = hidden if field == "scope" else "local"
    call = ToolCall(tool=tool, capability=capability, scope=scope)
    step_id = hidden if field == "step_id" else "read-step"
    deps = (hidden,) if field == "depends_on" else ()
    step = PlanStep(step_id=step_id, call=call, depends_on=deps)

    with pytest.raises(PlanConflictError, match="Unicode formatting control"):
        PlanGraph((step,))


def test_human_readable_unicode_stays_available_in_optional_planner():
    call = ToolCall(
        tool="検索ツール", capability="情報取得", scope="東京/ローカル",
    )
    step = PlanStep("計画-α", call)
    plan = PlanGraph((step,))
    assert set(plan.steps) == {"計画-α"}


def test_invisible_dependency_refused_even_without_matching_step():
    call = ToolCall(tool="mock.read", capability="read", scope="local")
    step = PlanStep("root", call, depends_on=("absent\u200dstep",))
    with pytest.raises(PlanConflictError, match="Unicode formatting control"):
        PlanGraph((step,))
