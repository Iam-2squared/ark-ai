"""Deep DAG failure propagation is linear, deterministic and replay-safe."""

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _step(label, *dependencies):
    return PlanStep(
        label,
        ToolCall("fixture.read", "fixture.cap", "synthetic:scope"),
        dependencies,
    )


def _fail_root(plan, root="root"):
    running = plan.transition(root, StepState.RUNNING, expected_revision=0)
    assert running.revision == 1
    failed = plan.transition(root, StepState.FAILED, expected_revision=1)
    assert failed.revision == 2


def test_deep_1500_step_chain_blocks_every_pending_descendant():
    steps = [_step("root")]
    for index in range(1, 1500):
        parent = "root" if index == 1 else f"step-{index - 1:04d}"
        steps.append(_step(f"step-{index:04d}", parent))
    plan = PlanGraph(tuple(steps))
    _fail_root(plan)
    statuses = plan.statuses()
    assert statuses["root"].state is StepState.FAILED
    assert all(
        statuses[f"step-{index:04d}"].state is StepState.BLOCKED
        and statuses[f"step-{index:04d}"].revision == 1
        for index in range(1, 1500)
    )
    assert plan.ready_steps() == ()


def test_diamond_and_shared_subtree_are_blocked_once():
    plan = PlanGraph(
        (
            _step("root"),
            _step("left", "root"),
            _step("right", "root"),
            _step("join", "left", "right"),
            _step("tail", "join"),
        )
    )
    _fail_root(plan)
    assert {key: value.revision for key, value in plan.statuses().items()} == {
        "root": 2,
        "left": 1,
        "right": 1,
        "join": 1,
        "tail": 1,
    }
    assert all(
        status.state is StepState.BLOCKED
        for key, status in plan.statuses().items()
        if key != "root"
    )


def test_unrelated_branch_retains_pending_and_readiness():
    plan = PlanGraph(
        (
            _step("root"),
            _step("blocked-one", "root"),
            _step("blocked-two", "blocked-one"),
            _step("independent"),
            _step("independent-child", "independent"),
        )
    )
    _fail_root(plan)
    statuses = plan.statuses()
    assert statuses["blocked-two"].state is StepState.BLOCKED
    assert statuses["independent"].state is StepState.PENDING
    assert statuses["independent-child"].state is StepState.PENDING
    assert tuple(step.step_id for step in plan.ready_steps()) == ("independent",)
