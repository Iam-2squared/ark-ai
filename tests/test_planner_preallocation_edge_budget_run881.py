"""PlanGraph must bound edge count before duplicate-set allocation.

No changes to the frozen PlanStep contract or terminal transition rules.
"""
import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, ToolCall


@pytest.mark.parametrize("edge_count", [65_537, 131_072])
def test_reflected_oversized_dependency_tuple_is_rejected_before_duplicate_scan(
    edge_count: int,
) -> None:
    call = ToolCall("fixture.read", "fixture.read", "local")
    step = PlanStep("root", call)
    # Simulate a caller mutating a frozen dataclass after its constructor
    # validated it; this tuple is exact but far beyond PlanGraph's edge cap.
    object.__setattr__(step, "depends_on", ("child",) * edge_count)
    with pytest.raises(ValueError, match="plan dependency budget exceeded"):
        PlanGraph((step,))


def test_in_budget_duplicate_dependencies_still_fail_closed() -> None:
    call = ToolCall("fixture.read", "fixture.read", "local")
    step = PlanStep("root", call)
    object.__setattr__(step, "depends_on", ("child", "child"))
    with pytest.raises(PlanConflictError, match="duplicate IDs"):
        PlanGraph((step,))
