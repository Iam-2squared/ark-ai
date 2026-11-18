"""Run962: optional PlanGraph input guards visually ambiguous Unicode controls.

No frozen ToolCall/PlanStep constructor, executable backend, or journal contract
is changed. Graphs are deterministic in-memory fixtures only.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph


_FORMAT_CONTROLS = (
    "\u0085", "\u061c", "\u200e", "\u200f",
    "\u2028", "\u2029", "\u202a", "\u202b", "\u202c",
    "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069",
)


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize(
    "field", ("step_id", "dependency", "tool", "capability", "scope"),
)
def test_graph_rejects_invisible_direction_and_line_controls(
    control: str, field: str,
) -> None:
    injected = "left" + control + "right"
    call = ToolCall(
        injected if field == "tool" else "fixture.read",
        injected if field == "capability" else "fixture.read",
        injected if field == "scope" else "local-only",
    )
    steps = (
        PlanStep(
            injected if field == "step_id" else "root",
            call,
            (injected,) if field == "dependency" else (),
        ),
    )
    with pytest.raises(PlanConflictError, match="Unicode formatting control"):
        PlanGraph(steps)


@pytest.mark.parametrize("field", ("step_id", "scope"))
def test_reflected_format_identity_denied_before_graph_hash(field: str) -> None:
    call = ToolCall("fixture.read", "fixture.read", "local-only")
    step = PlanStep("root", call)
    if field == "step_id":
        object.__setattr__(step, "step_id", "root\u202ealien")
    else:
        object.__setattr__(call, "scope", "local\u2067spoof")
    with pytest.raises(PlanConflictError, match="Unicode formatting control"):
        PlanGraph((step,))


def test_multilingual_graph_without_format_controls_still_admitted() -> None:
    call = ToolCall("fixture.測定", "offline.温度", "private/שלום")
    graph = PlanGraph((
        PlanStep("根-مرحبا", call),
        PlanStep("処理-二", call, ("根-مرحبا",)),
    ))
    assert [step.step_id for step in graph.ready_steps()] == ["根-مرحبا"]
    assert graph.topology_digest().startswith("plan_")
