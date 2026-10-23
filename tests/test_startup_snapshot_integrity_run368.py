"""Cached startup readiness witnesses fail closed after reflected mutations.

This is a disconnected synthetic diagnostic, not external attestation or
authorization of real tools, accounts, clocks or devices.
"""

from dataclasses import replace

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _snapshot():
    return evaluate_startup_readiness(
        (
            StartupComponent(
                "planner", ("memory",), ReadinessState.READY,
                schema_revision="synthetic-1",
            ),
            StartupComponent(
                "memory", (), ReadinessState.BLOCKED,
                failure_code="synthetic-unavailable",
            ),
        )
    )


def test_original_snapshot_diagnostics_unchanged():
    snapshot = _snapshot()
    assert snapshot.state("memory") is ReadinessState.BLOCKED
    assert snapshot.state("planner") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("planner") == ("memory",)


@pytest.mark.parametrize(
    ("field_name", "new_value"),
    [
        ("effective_state", ReadinessState.READY),
        ("local_state", ReadinessState.READY),
        ("failure_code", None),
        ("schema_revision", "forged"),
        ("dependencies", ("planner",)),
        ("component_id", "renamed-memory"),
    ],
)
def test_reflective_mutation_of_cached_result_is_rejected(field_name, new_value):
    snapshot = _snapshot()
    item = snapshot.components[0]
    object.__setattr__(item, field_name, new_value)
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.state("planner")
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.root_blockers("planner")


def test_digest_mutation_is_rejected():
    snapshot = _snapshot()
    object.__setattr__(snapshot, "digest", "startup_" + "0" * 64)
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.state("planner")


def test_tuple_reordering_is_rejected():
    snapshot = _snapshot()
    object.__setattr__(snapshot, "components", tuple(reversed(snapshot.components)))
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.root_blockers("planner")


def test_snapshot_container_replacement_is_rejected():
    snapshot = _snapshot()
    object.__setattr__(snapshot, "components", list(snapshot.components))
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.state("planner")


def test_witness_changes_when_valid_input_changes():
    original = _snapshot()
    another = evaluate_startup_readiness(
        (
            StartupComponent("planner", ("memory",), ReadinessState.READY),
            StartupComponent("memory", (), ReadinessState.READY),
        )
    )
    assert original.digest != another.digest
    assert another.state("planner") is ReadinessState.READY
