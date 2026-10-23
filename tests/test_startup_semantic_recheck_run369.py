"""Recomputed local digest must not conceal a contradictory readiness graph."""

import hashlib
import json

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _snapshot():
    return evaluate_startup_readiness(
        (
            StartupComponent("memory", local_state=ReadinessState.BLOCKED),
            StartupComponent("planner", ("memory",)),
            StartupComponent("tools", ("planner",)),
            StartupComponent("conversation"),
        )
    )


def _recompute_local_digest(snapshot):
    """Intentionally emulate an in-process actor able to rewrite the digest."""
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
            for item in snapshot.components
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    object.__setattr__(
        snapshot, "digest", "startup_" + hashlib.sha256(encoded).hexdigest()
    )


@pytest.mark.parametrize(
    ("component", "field", "replacement"),
    [
        ("planner", "effective_state", ReadinessState.READY),
        ("tools", "effective_state", ReadinessState.READY),
        ("planner", "local_state", ReadinessState.DEPENDENCY_BLOCKED),
        ("planner", "dependencies", ("absent",)),
        ("memory", "dependencies", ("tools",)),
        ("memory", "component_id", " "),
        ("memory", "failure_code", " "),
    ],
)
def test_recomputed_digest_does_not_authorize_inconsistent_cached_graph(
    component, field, replacement,
):
    snapshot = _snapshot()
    item = next(x for x in snapshot.components if x.component_id == component)
    object.__setattr__(item, field, replacement)
    _recompute_local_digest(snapshot)
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.state("conversation")
    with pytest.raises(ValueError, match="startup snapshot"):
        snapshot.root_blockers("tools")


def test_valid_independent_lane_and_derived_chain_still_work():
    snapshot = _snapshot()
    assert snapshot.state("conversation") is ReadinessState.READY
    assert snapshot.state("planner") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.state("tools") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("tools") == ("memory",)
