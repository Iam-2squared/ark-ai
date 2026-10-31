"""Synthetic CI pipelining must never imply execution or spending permission."""

from dataclasses import FrozenInstanceError

import pytest

from ark.agency_synthetic_lane_selector_review import (
    SyntheticLaneSelectionRejected,
    SyntheticWorkLane,
    review_disconnected_work_lanes,
)


def _lane(name="planner", *, touches=("src/ark/agency/planner.py",),
          priority=10, depends_on=(), requires_green=(),
          cost_class="free_local", requires_approval=False, reversible=True):
    return SyntheticWorkLane(
        name, priority, touches, depends_on, requires_green,
        cost_class, requires_approval, reversible,
    )


def test_independent_lanes_selected_deterministically_and_denied_execution():
    lanes = (_lane(), _lane("memory", touches=("src/ark/memory",), priority=20))
    result = review_disconnected_work_lanes(lanes)
    again = review_disconnected_work_lanes(tuple(reversed(lanes)))
    assert result == again
    assert result.selected == ("memory", "planner")
    assert result.deferred == ()
    assert result.diagnostic_digest.startswith("lanes_")
    assert not result.execution_authorized
    assert not result.github_write_authorized
    assert not result.spending_authorized
    with pytest.raises(FrozenInstanceError):
        result.selected = ()


def test_inflight_ci_changes_route_work_to_independent_module():
    lanes = (_lane(), _lane("memory", touches=("src/ark/memory",), priority=7))
    result = review_disconnected_work_lanes(
        lanes, inflight_paths=("src/ark/agency",),
    )
    assert result.selected == ("memory",)
    assert result.deferred == (("planner", "inflight_ci_conflict"),)


def test_filename_prefix_is_not_false_collision():
    lanes = (
        _lane("a", touches=("src/pkg/x.py",)),
        _lane("b", touches=("src/pkg/x.py2",)),
    )
    assert review_disconnected_work_lanes(lanes).selected == ("a", "b")


@pytest.mark.parametrize("cost", ("potentially_billable", "unknown"))
def test_paid_or_unknown_lane_cannot_be_selected(cost):
    result = review_disconnected_work_lanes((_lane(cost_class=cost),))
    assert not result.selected
    assert result.deferred[0][1] == "cost_unapproved"


def test_user_approval_and_irreversible_choice_are_blocked():
    lanes = (
        _lane("approval", touches=("doc/a.txt",), requires_approval=True),
        _lane("irreversible", touches=("doc/b.txt",), reversible=False),
    )
    result = review_disconnected_work_lanes(lanes)
    assert result.selected == ()
    assert dict(result.deferred) == {
        "approval": "explicit_approval_required", "irreversible": "irreversible",
    }


def test_dependency_and_head_gate_must_be_caller_supplied():
    first = _lane("foundation", touches=("src/a.py",), priority=5)
    next_one = _lane(
        "dependent", touches=("src/b.py",), priority=10,
        depends_on=("foundation",), requires_green=("run1234",),
    )
    still = review_disconnected_work_lanes((first, next_one))
    assert still.selected == ("foundation",)
    assert dict(still.deferred)["dependent"] == "dependencies_unfinished"
    unverified = review_disconnected_work_lanes(
        (first, next_one), completed=frozenset(("foundation",)),
    )
    assert unverified.selected == ()
    assert dict(unverified.deferred)["dependent"] == "exact_head_green_unverified"
    claimed = review_disconnected_work_lanes(
        (first, next_one), completed=frozenset(("foundation",)),
        claimed_green=frozenset(("run1234",)),
    )
    assert claimed.selected == ("dependent",)
    assert not claimed.execution_authorized  # external CI proof is not authenticated here


def test_conflicting_lanes_held_even_when_priorities_differ():
    lanes = (
        _lane("a", priority=30, touches=("src/ark",)),
        _lane("b", priority=20, touches=("src/ark/agency",)),
        _lane("c", priority=10, touches=("docs/plan.md",)),
    )
    result = review_disconnected_work_lanes(lanes, max_selected=2)
    assert result.selected == ("a", "c")
    assert result.deferred == (("b", "selected_lane_conflict"),)


def test_capacity_excess_lanes_deferred_in_deterministic_priority_order():
    lanes = tuple(_lane(f"lane{i}", priority=10-i, touches=(f"src/f{i}.py",))
                  for i in range(4))
    result = review_disconnected_work_lanes(lanes, max_selected=2)
    assert result.selected == ("lane0", "lane1")
    assert dict(result.deferred) == {"lane2": "session_capacity", "lane3": "session_capacity"}


@pytest.mark.parametrize("bad", (
    (_lane("same"), _lane("same", touches=("src/b.py",))),
    (_lane("a", depends_on=("missing",)),),
    (_lane("a", depends_on=("b",)), _lane("b", depends_on=("a",))),
    (_lane("a", depends_on=("a",)),),
))
def test_invalid_dependency_graph_rejected(bad):
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes(bad)


@pytest.mark.parametrize("bad_path", (
    "../secret", "src//secret", "src/./file", "src/../file",
    "src\\win", "C:/absolute", "/absolute", ".git/config",
))
def test_unsafe_touched_path_is_rejected(bad_path):
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(touches=(bad_path,)),))


def test_unknown_exact_types_and_empty_inflight_strings_rejected():
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(priority=True),))
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(cost_class="free_unknown"),))
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(),), max_selected=True)
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(),), inflight_paths=("",))
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(),), completed=frozenset(("unknown",)))


def test_bounded_inputs_reject_excessive_lanes_and_touches():
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes(tuple(_lane(f"l{i}") for i in range(129)))
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes((_lane(touches=tuple(
            f"src/f{i}.py" for i in range(17))),))
