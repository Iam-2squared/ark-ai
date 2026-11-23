"""Run1183: complete Unicode format-control admission for PlanGraph labels."""

from __future__ import annotations

import pytest

from ark.agency import (
    PlanConflictError,
    PlanGraph,
    PlanStep,
    StepState,
    ToolCall,
    planner,
)


def _steps() -> tuple[PlanStep, PlanStep]:
    root = PlanStep("root", ToolCall("mock.read", "mock.read", "local:fixtures"))
    leaf = PlanStep(
        "leaf",
        ToolCall("mock.read", "mock.read", "local:fixtures"),
        depends_on=("root",),
    )
    return root, leaf


@pytest.mark.parametrize("control", ("\u0600", "\ufff9", "\U000e0001"))
@pytest.mark.parametrize("field", ("step_id", "dependency", "tool", "capability", "scope"))
def test_plan_graph_rejects_every_unicode_format_control_in_identity_fields(
    control: str, field: str,
) -> None:
    root, leaf = _steps()
    label = "identity" + control + "tail"
    if field == "step_id":
        object.__setattr__(root, "step_id", label)
    elif field == "dependency":
        object.__setattr__(leaf, "depends_on", (label,))
    else:
        object.__setattr__(root.call, field, label)

    with pytest.raises(
        PlanConflictError,
        match="Unicode formatting control",
    ):
        PlanGraph((root, leaf))


@pytest.mark.parametrize("control", ("\u0600", "\ufff9", "\U000e0001"))
def test_transition_rejects_unicode_format_control_before_status_mutation(
    control: str,
) -> None:
    graph = PlanGraph(_steps())

    with pytest.raises(
        PlanConflictError,
        match="Unicode formatting control",
    ):
        graph.transition(
            "root" + control,
            StepState.RUNNING,
            expected_revision=0,
        )

    assert graph.statuses()["root"].state is StepState.PENDING
    assert graph.statuses()["root"].revision == 0


def test_plan_graph_keeps_ordinary_multilingual_labels_valid() -> None:
    graph = PlanGraph((
        PlanStep(
            "予定",
            ToolCall("mock.read", "mock.read", "local:fixtures"),
        ),
    ))

    assert tuple(step.step_id for step in graph.ready_steps()) == ("予定",)


@pytest.mark.parametrize("dependency", ("module", "category"))
def test_replaced_unicode_dependency_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    called: list[str] = []

    def forbidden(_character: str) -> str:
        called.append("category")
        raise AssertionError("unreviewed Unicode classifier received graph text")

    if dependency == "module":
        class PoisonedUnicodeDependency:
            @property
            def category(self) -> str:
                called.append("category")
                raise AssertionError("replaced Unicode module was inspected")

        monkeypatch.setattr(
            planner, "unicodedata", PoisonedUnicodeDependency(),
        )
    else:
        # Patch the Planner's captured function binding rather than mutating
        # the process-global unicodedata module used by pytest's own renderer.
        monkeypatch.setattr(planner, "_ORIGINAL_UNICODE_CATEGORY", forbidden)

    with pytest.raises(PlanConflictError, match="Unicode policy changed"):
        PlanGraph(_steps())

    assert called == []
