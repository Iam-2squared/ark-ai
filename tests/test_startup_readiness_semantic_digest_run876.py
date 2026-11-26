"""Re-hashed but semantically forged readiness snapshots must fail closed.

All probes are synthetic local diagnostics; READY is not an activation grant.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from ark.startup_readiness_review import (
    ComponentResult,
    ReadinessState,
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _baseline() -> StartupSnapshot:
    return evaluate_startup_readiness((
        StartupComponent("parent", local_state=ReadinessState.BLOCKED),
        StartupComponent("child", ("parent",)),
        StartupComponent("independent", local_state=ReadinessState.DEGRADED),
    ))


def _validly_rehashed(components: tuple[ComponentResult, ...]) -> StartupSnapshot:
    """A forged digest alone must not make a contradictory graph trustworthy."""
    payload = {
        "schema_version": 1,
        "components": [
            {
                "id": item.component_id,
                "dependencies": item.dependencies,
                "local": item.local_state.value,
                "effective": item.effective_state.value,
                "failure_code": item.failure_code,
                "schema_revision": item.schema_revision,
            }
            for item in components
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return StartupSnapshot(
        components, "startup_" + hashlib.sha256(encoded).hexdigest(),
    )


@pytest.mark.parametrize(
    "forged_state",
    (
        ReadinessState.READY,
        ReadinessState.DEGRADED,
        ReadinessState.BLOCKED,
    ),
)
def test_cannot_rehash_blocked_child_as_another_state(
    forged_state: ReadinessState,
) -> None:
    initial = _baseline()
    forged = _validly_rehashed(tuple(
        replace(item, effective_state=forged_state)
        if item.component_id == "child" else item
        for item in initial.components
    ))
    with pytest.raises(ValueError, match="effective state"):
        forged.state("child")
    with pytest.raises(ValueError, match="effective state"):
        forged.root_blockers("child")


def test_rehashed_unknown_dependency_is_still_invalid() -> None:
    initial = _baseline()
    forged = _validly_rehashed(tuple(
        replace(item, dependencies=("missing",))
        if item.component_id == "child" else item
        for item in initial.components
    ))
    with pytest.raises(ValueError, match="dependency"):
        forged.state("child")


def test_rehashed_dependency_cycle_is_never_ready() -> None:
    initial = _baseline()
    forged = _validly_rehashed(tuple(
        replace(item, dependencies=("child",))
        if item.component_id == "parent" else item
        for item in initial.components
    ))
    with pytest.raises(ValueError, match="cycle"):
        forged.state("child")


def test_readiness_identifier_rejects_overlong_utf8_bytes() -> None:
    with pytest.raises(ValueError, match="256 UTF-8 bytes"):
        StartupComponent("国" * 100)


def test_valid_blocked_ancestry_and_independent_degradation_unchanged() -> None:
    observed = _baseline()
    assert observed.state("child") is ReadinessState.DEPENDENCY_BLOCKED
    assert observed.root_blockers("child") == ("parent",)
    assert observed.state("independent") is ReadinessState.DEGRADED
    assert observed.root_blockers("independent") == ()
