"""Fresh exact-schema startup claims are diagnostic only, never authority."""

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
    review_synthetic_startup_lease,
)
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _snapshot(*, memory=ReadinessState.READY, planner=ReadinessState.READY):
    return evaluate_startup_readiness((
        StartupComponent("memory", local_state=memory, schema_revision="memory-1"),
        StartupComponent(
            "planner", ("memory",), local_state=planner, schema_revision="planner-1",
        ),
        StartupComponent("conversation", schema_revision="chat-1"),
    ))


def _requirements():
    return (
        SyntheticReadinessRequirement("planner", "planner-1"),
        SyntheticReadinessRequirement("memory", "memory-1"),
    )


def _review(snapshot=None, requirements=None, **changes):
    if snapshot is None:
        snapshot = _snapshot()
    if requirements is None:
        requirements = _requirements()
    values = {"captured_at_ms": 10, "now_ms": 12, "max_age_ms": 5}
    values.update(changes)
    return review_synthetic_startup_lease(snapshot, requirements, **values)


def test_valid_exact_schema_and_dependency_review_is_never_activation():
    result = _review()
    assert result.required_components == ("memory", "planner")
    assert result.snapshot_digest.startswith("startup_")
    assert result.checked_at_ms == 12
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False


@pytest.mark.parametrize("now", [-1, 9, 16, 2**63, True])
def test_stale_invalid_or_regressing_clock_denied(now):
    with pytest.raises(SyntheticStartupLeaseRejected):
        _review(now_ms=now)


def test_exact_freshness_boundary_allowed():
    assert _review(now_ms=15).checked_at_ms == 15


@pytest.mark.parametrize("captured,max_age", [(-1, 5), (True, 5), (11, -1), (1, True)])
def test_invalid_lease_clock_inputs_denied(captured, max_age):
    with pytest.raises(SyntheticStartupLeaseRejected):
        _review(captured_at_ms=captured, max_age_ms=max_age)


@pytest.mark.parametrize("state", [ReadinessState.BLOCKED, ReadinessState.DEGRADED])
def test_required_memory_not_ready_denied_even_with_independent_chat(state):
    snapshot = _snapshot(memory=state)
    assert snapshot.state("conversation") is ReadinessState.READY
    with pytest.raises(SyntheticStartupLeaseRejected, match="blocked, degraded"):
        _review(snapshot)


def test_planner_degraded_state_denied_even_if_memory_ready():
    with pytest.raises(SyntheticStartupLeaseRejected, match="blocked, degraded"):
        _review(_snapshot(planner=ReadinessState.DEGRADED))


def test_unknown_component_or_wrong_schema_denied():
    with pytest.raises(SyntheticStartupLeaseRejected, match="not present"):
        _review(requirements=(SyntheticReadinessRequirement("missing", "v1"),))
    with pytest.raises(SyntheticStartupLeaseRejected, match="schema-stale"):
        _review(requirements=(SyntheticReadinessRequirement("memory", "memory-2"),))


def test_duplicate_or_missing_requirements_denied():
    with pytest.raises(SyntheticStartupLeaseRejected, match="duplicate"):
        _review(requirements=_requirements() + _requirements()[:1])
    with pytest.raises(SyntheticStartupLeaseRejected, match="exact"):
        _review(requirements=())
    with pytest.raises(SyntheticStartupLeaseRejected, match="exact"):
        _review(requirements=list(_requirements()))


@pytest.mark.parametrize(
    "bad",
    [
        SyntheticReadinessRequirement("", "v1"),
        SyntheticReadinessRequirement("memory", " "),
        SyntheticReadinessRequirement("memory", "v" * 257),
        SyntheticReadinessRequirement("memory", 1),
    ],
)
def test_bad_requirement_ids_and_schema_are_denied(bad):
    with pytest.raises(SyntheticStartupLeaseRejected):
        _review(requirements=(bad,))


def test_reflected_snapshot_tamper_denied_even_when_digest_is_unchanged():
    snapshot = _snapshot()
    item = snapshot.components[0]
    object.__setattr__(item, "schema_revision", "forged")
    with pytest.raises(SyntheticStartupLeaseRejected, match="integrity"):
        _review(snapshot)


def test_new_snapshot_after_probe_change_requires_fresh_revision_review():
    first = _snapshot()
    changed = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-2"),
        StartupComponent("planner", ("memory",), schema_revision="planner-1"),
    ))
    assert first.digest != changed.digest
    with pytest.raises(SyntheticStartupLeaseRejected, match="schema-stale"):
        _review(changed)


def test_unrelated_blocked_lane_does_not_poison_required_ready_lane():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent("planner", ("memory",), schema_revision="planner-1"),
        StartupComponent("camera", local_state=ReadinessState.BLOCKED),
    ))
    assert _review(snapshot).required_components == ("memory", "planner")
    assert snapshot.state("camera") is ReadinessState.BLOCKED
