"""Bounded, caller-controlled startup probe iterators must remain coherent.

Synthetic readiness never authenticates a user, device, clock or backend.
"""

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize(
    "mutation",
    (
        "component_id", "local_state", "dependencies",
        "failure_code", "schema_revision",
    ),
)
def test_earlier_yielded_probe_cannot_drift_and_restore_before_exhaustion(
    mutation,
):
    root = StartupComponent("root", local_state=ReadinessState.BLOCKED)
    parent = StartupComponent(
        "parent", ("root",), ReadinessState.READY, "offline", "revision-1",
    )
    child = StartupComponent("child", ("parent",))
    options = {
        "component_id": "forged-parent",
        "local_state": ReadinessState.DEGRADED,
        "dependencies": tuple(list(parent.dependencies)),
        "failure_code": "forged-code",
        "schema_revision": "forged-revision",
    }
    original = getattr(parent, mutation)
    yielded = []

    def probes():
        yield root
        yield parent
        object.__setattr__(parent, mutation, options[mutation])
        yielded.append("modified")
        yield child
        object.__setattr__(parent, mutation, original)
        yielded.append("restored")

    with pytest.raises(ValueError, match="startup input changed"):
        evaluate_startup_readiness(probes())
    assert yielded == ["modified"]
    object.__setattr__(parent, mutation, original)
    safe = evaluate_startup_readiness((root, parent, child))
    assert safe.state("child") is ReadinessState.DEPENDENCY_BLOCKED


def test_generator_input_budget_enforced_before_extra_elements_consumed():
    produced = 0

    def probes():
        nonlocal produced
        for number in range(15_000):
            produced += 1
            yield StartupComponent(f"offline-{number}")

    with pytest.raises(ValueError, match="budget"):
        evaluate_startup_readiness(probes())
    assert produced == 10_001


def test_unchanged_generator_preserves_required_blocker():
    root = StartupComponent("root", local_state=ReadinessState.BLOCKED)
    child = StartupComponent("child", ("root",))
    snapshot = evaluate_startup_readiness(x for x in (root, child))
    assert snapshot.state("root") is ReadinessState.BLOCKED
    assert snapshot.state("child") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("child") == ("root",)
