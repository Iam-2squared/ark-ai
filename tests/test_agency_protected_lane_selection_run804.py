"""A caller's frozen paths are excluded from disconnected work proposals.

This is a synthetic schedule, not approval to write GitHub, pay, or dispatch.
"""

import pytest

from ark.agency_synthetic_lane_selector_review import (
    SyntheticLaneSelectionRejected,
    SyntheticWorkLane,
    review_disconnected_work_lanes,
)


def _lane(name: str, touch: str, *, priority: int = 10) -> SyntheticWorkLane:
    return SyntheticWorkLane(
        name, priority, (touch,), (), (), "free_local", False, True,
    )


def test_frozen_frontend_and_local_ui_subtrees_withhold_only_ui_work():
    lanes = (
        _lane("frontend", "frontend/src/app.tsx", priority=40),
        _lane("local_ui", "src/ark/ui/server.py", priority=30),
        _lane("screenshots", "docs/next-ui/example.jpg", priority=20),
        _lane("memory", "src/ark/memory/sqlite_store.py", priority=10),
    )
    result = review_disconnected_work_lanes(
        lanes,
        protected_paths=("docs/next-ui", "frontend", "src/ark/ui"),
    )
    assert result.selected == ("memory",)
    assert result.deferred == (
        ("frontend", "protected_path"),
        ("local_ui", "protected_path"),
        ("screenshots", "protected_path"),
    )
    assert result.execution_authorized is False
    assert result.github_write_authorized is False
    assert result.spending_authorized is False


def test_parent_folder_cannot_be_selected_around_a_protected_child():
    lanes = (
        _lane("broad", "src/ark"),
        _lane("sibling", "src/ark2/agency.py"),
    )
    outcome = review_disconnected_work_lanes(
        lanes, protected_paths=("src/ark/ui",),
    )
    assert outcome.selected == ("sibling",)
    assert outcome.deferred == (("broad", "protected_path"),)


def test_prefix_sibling_is_not_falsely_protected():
    outcome = review_disconnected_work_lanes(
        (_lane("other", "frontend2/index.ts"),),
        protected_paths=("frontend",),
    )
    assert outcome.selected == ("other",)


def test_unprotected_result_remains_same_with_empty_protected_paths():
    lanes = (_lane("planner", "src/ark/agency/planner.py"),)
    baseline = review_disconnected_work_lanes(lanes)
    explicit = review_disconnected_work_lanes(lanes, protected_paths=())
    assert explicit == baseline


def test_protected_path_decision_is_order_independent_and_hash_bound():
    lanes = (
        _lane("read", "src/ark/observation_window_review.py", priority=2),
        _lane("paused", "frontend/app.ts", priority=1),
    )
    protected = review_disconnected_work_lanes(
        lanes, protected_paths=("frontend",),
    )
    reversed_lanes = review_disconnected_work_lanes(
        tuple(reversed(lanes)), protected_paths=("frontend",),
    )
    unprotected = review_disconnected_work_lanes(lanes)
    assert protected == reversed_lanes
    assert protected.diagnostic_digest != unprotected.diagnostic_digest
    assert protected.selected == ("read",)
    assert protected.deferred == (("paused", "protected_path"),)


@pytest.mark.parametrize("bad_paths", (
    ["frontend"],
    ("frontend", "frontend"),
    ("frontend/../src",),
    ("frontend//app",),
    ("src/ark/ui", "docs/next-ui"),
    tuple(f"src/p{i}" for i in range(17)),
))
def test_untrusted_protected_path_input_is_rejected(bad_paths):
    with pytest.raises(SyntheticLaneSelectionRejected):
        review_disconnected_work_lanes(
            (_lane("core", "src/ark/memory/sqlite_store.py"),),
            protected_paths=bad_paths,
        )


def test_protected_lane_cannot_be_unblocked_by_claimed_ci_green():
    lanes = (_lane("paused", "frontend/src/app.tsx"),)
    result = review_disconnected_work_lanes(
        lanes, claimed_green=frozenset(("all-green",)),
        protected_paths=("frontend",),
    )
    assert result.selected == ()
    assert result.deferred == (("paused", "protected_path"),)


def test_completed_lane_does_not_gain_execution_authority():
    lanes = (_lane("old", "frontend/index.html"),)
    result = review_disconnected_work_lanes(
        lanes, completed=frozenset(("old",)),
        protected_paths=("frontend",),
    )
    assert result.selected == ()
    assert result.deferred == (("old", "already_completed"),)
    assert result.execution_authorized is False
