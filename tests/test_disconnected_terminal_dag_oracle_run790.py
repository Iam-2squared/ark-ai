"""Exhaustive finite-state oracle for disconnected Planner failure propagation.

Enumerates all 32 declared-failure subsets across four five-step DAGs. The
oracle does not call a backend, authorize WRITE or infer real execution.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule
from ark.agency.disconnected_batch_terminal_projection import (
    DisconnectedBatchTerminalRejected,
    project_disconnected_batch_terminals,
    verify_disconnected_batch_terminals,
)

_IDS = tuple(f"step_{index:016x}" for index in range(1, 6))
_REQUEST = "req_" + "d" * 32
# Each dependency index precedes its child. Multiple wave shapes matter:
# independent, serial, join, and diamond-plus-isolated step.
_GRAPHS = (
    ((), (), (), (), ()),
    ((), (0,), (1,), (2,), (3,)),
    ((), (), (0, 1), (2,), ()),
    ((), (0,), (0,), (1, 2), ()),
)


def _oracle(
    graph: tuple[tuple[int, ...], ...], failures: tuple[str, ...],
) -> tuple[tuple[str, str], ...] | None:
    """Independent sequential dependency oracle; None means impossible claim."""
    fail = set(failures)
    states: dict[int, str] = {}
    for index, dependencies in enumerate(graph):
        blocked = any(states[dependency] != "SUCCEEDED" for dependency in dependencies)
        if blocked and _IDS[index] in fail:
            return None  # A blocked descendant cannot also have executed and failed.
        states[index] = (
            "BLOCKED" if blocked else
            "FAILED" if _IDS[index] in fail else "SUCCEEDED"
        )
    return tuple((_IDS[index], states[index]) for index in range(5))


@pytest.mark.parametrize("graph", _GRAPHS)
@pytest.mark.parametrize("mask", range(32))
def test_all_detached_failure_subsets_match_independent_oracle(graph, mask):
    steps = tuple(
        DisconnectedBatchStep(
            _IDS[index], "math.sum", '{"values":[1]}',
            tuple(_IDS[dep] for dep in graph[index]),
        )
        for index in range(5)
    )
    plan = build_disconnected_batch_plan(_REQUEST, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    failures = tuple(
        _IDS[index] for index in range(5) if mask & (1 << index)
    )
    expected = _oracle(graph, failures)
    if expected is None:
        with pytest.raises(DisconnectedBatchTerminalRejected):
            project_disconnected_batch_terminals(
                plan, schedule, retained_digest=plan.plan_digest,
                failed_step_ids=failures,
            )
    else:
        projection = project_disconnected_batch_terminals(
            plan, schedule, retained_digest=plan.plan_digest,
            failed_step_ids=failures,
        )
        assert projection.terminal_states == expected
        assert len(projection.projection_digest) == 64
        assert verify_disconnected_batch_terminals(
            projection, plan, schedule, retained_digest=plan.plan_digest,
        ) is None
        assert projection.dispatch_authorized is False
        assert projection.write_authorized is False
        assert projection.automatic_replay_authorized is False
        assert projection.failure_claim_authenticated is False
