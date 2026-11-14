"""Import-time readiness budgets cannot be widened by in-process mutation.

These are disconnected synthetic graph fixtures, never capability grants,
hardware readiness attestations, or authorization to dispatch a backend.
"""

from __future__ import annotations

import pytest

import ark.startup_readiness_review as readiness


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_MAX_COMPONENTS", 100_000),
        ("_MAX_COMPONENTS", True),
        ("_MAX_DEPENDENCIES_PER_COMPONENT", 40_960),
        ("_MAX_DEPENDENCIES_PER_COMPONENT", False),
        ("_MAX_DEPENDENCY_EDGES", 655_360),
        ("_MAX_DEPENDENCY_EDGES", "65536"),
    ),
)
def test_modified_budget_rejected_before_generator_or_cached_ready(
    monkeypatch, name: str, replacement: object,
) -> None:
    root = readiness.StartupComponent("memory")
    cached = readiness.evaluate_startup_readiness((root,))
    consumed: list[str] = []

    def stream():
        consumed.append("untrusted iterator consumed")
        yield root

    monkeypatch.setattr(readiness, name, replacement)
    with pytest.raises(ValueError, match="readiness admission budgets changed"):
        readiness.evaluate_startup_readiness(stream())
    assert consumed == []
    with pytest.raises(ValueError, match="readiness admission budgets changed"):
        cached.state("memory")
    with pytest.raises(ValueError, match="readiness admission budgets changed"):
        cached.root_blockers("memory")
    with pytest.raises(ValueError, match="readiness admission budgets changed"):
        readiness.StartupComponent("new")


def test_generator_cannot_widen_budget_between_yields(monkeypatch) -> None:
    root = readiness.StartupComponent("root")
    child = readiness.StartupComponent("child", ("root",))
    yielded: list[str] = []

    def stream():
        yielded.append("root")
        yield root
        monkeypatch.setattr(readiness, "_MAX_COMPONENTS", 100_000)
        yielded.append("child")
        yield child

    with pytest.raises(ValueError, match="readiness admission budgets changed"):
        readiness.evaluate_startup_readiness(stream())
    assert yielded == ["root", "child"]


def test_replaced_budget_checker_refused_before_probe_iteration(monkeypatch) -> None:
    root = readiness.StartupComponent("root")
    called: list[object] = []
    original = readiness._require_original_readiness_budgets

    def hostile():
        called.append("invoked")
        raise AssertionError("substituted budget checker ran")

    monkeypatch.setattr(readiness, "_require_original_readiness_budgets", hostile)
    with pytest.raises(ValueError, match="readiness admission budgets changed"):
        readiness.evaluate_startup_readiness(iter((root,)))
    assert called == []
    assert original is not hostile


def test_unmodified_readiness_propagation_stays_inert() -> None:
    snapshot = readiness.evaluate_startup_readiness((
        readiness.StartupComponent(
            "memory", local_state=readiness.ReadinessState.BLOCKED,
        ),
        readiness.StartupComponent("planner", ("memory",)),
        readiness.StartupComponent("independent"),
    ))
    assert snapshot.state("planner") is readiness.ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("planner") == ("memory",)
    assert snapshot.state("independent") is readiness.ReadinessState.READY
