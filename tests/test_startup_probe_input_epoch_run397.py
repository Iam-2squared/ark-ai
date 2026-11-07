"""Startup graph probes must remain the same original inputs while cloned.

READY and BLOCKED are caller-supplied fixture diagnoses, never permission
to open hardware, trust a real clock, or dispatch a backend.
"""

import pytest

import ark.startup_readiness_review as startup
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _graph():
    root = StartupComponent("root", local_state=ReadinessState.BLOCKED)
    parent = StartupComponent(
        "parent", ("root",), ReadinessState.READY,
        "offline-fixture", "revision-1",
    )
    child = StartupComponent("child", ("parent",))
    late = StartupComponent("late", ("child",))
    return root, parent, child, late


@pytest.mark.parametrize(
    "mutation",
    (
        "component_id", "local_state", "dependencies",
        "failure_code", "schema_revision",
    ),
)
def test_previous_probe_cannot_change_during_later_validation(
    monkeypatch, mutation,
):
    graph = _graph()
    parent = graph[1]
    replacement = {
        "component_id": "forged-parent",
        "local_state": ReadinessState.DEGRADED,
        "dependencies": tuple(list(parent.dependencies)),
        "failure_code": "forged-code",
        "schema_revision": "forged-revision",
    }[mutation]
    original_value = getattr(parent, mutation)
    identifier = startup._identifier
    injected = False

    def attack(value, label):
        nonlocal injected
        result = identifier(value, label)
        if not injected and label == "component_id" and value == "child":
            injected = True
            object.__setattr__(parent, mutation, replacement)
        return result

    monkeypatch.setattr(startup, "_identifier", attack)
    with pytest.raises(ValueError, match="startup input changed"):
        evaluate_startup_readiness(graph)
    assert injected
    object.__setattr__(parent, mutation, original_value)
    monkeypatch.setattr(startup, "_identifier", identifier)
    clean = evaluate_startup_readiness(graph)
    assert clean.state("parent") is ReadinessState.DEPENDENCY_BLOCKED
    assert clean.state("late") is ReadinessState.DEPENDENCY_BLOCKED


def test_transient_probe_mutation_cannot_hide_by_later_restoration(monkeypatch):
    graph = _graph()
    parent = graph[1]
    identifier = startup._identifier
    seen = []

    def attack(value, label):
        result = identifier(value, label)
        if label == "component_id" and value == "child":
            object.__setattr__(parent, "local_state", ReadinessState.DEGRADED)
            seen.append("mutated")
        if label == "component_id" and value == "late":
            object.__setattr__(parent, "local_state", ReadinessState.READY)
            seen.append("restored")
        return result

    monkeypatch.setattr(startup, "_identifier", attack)
    with pytest.raises(ValueError, match="startup input changed"):
        evaluate_startup_readiness(graph)
    assert seen == ["mutated"]
