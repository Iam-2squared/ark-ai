"""A local READY digest cannot disguise swapped or mutated component carriers."""

from dataclasses import replace

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
    review_synthetic_startup_lease,
)
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _state():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent(
            "scheduler", ("memory",), schema_revision="scheduler-v1",
        ),
    ))
    requirement = SyntheticReadinessRequirement("memory", "memory-v1")
    return snapshot, requirement


def _review(snapshot, requirement):
    return review_synthetic_startup_lease(
        snapshot, (requirement,),
        captured_at_ms=100, now_ms=101, max_age_ms=5,
    )


@pytest.mark.parametrize("phase", (1, 2))
@pytest.mark.parametrize(
    "change", ("tuple", "component", "dependencies", "local_state"),
)
def test_integrity_callback_cannot_substitute_snapshot_carriers(
    monkeypatch, phase, change,
):
    snapshot, requirement = _state()
    original = StartupSnapshot._assert_integrity
    calls = 0

    def substituted(self):
        nonlocal calls
        original(self)
        calls += 1
        if calls != phase:
            return
        if change == "tuple":
            object.__setattr__(self, "components", tuple(list(self.components)))
        elif change == "component":
            entries = list(self.components)
            entries[0] = replace(entries[0])
            object.__setattr__(self, "components", tuple(entries))
        elif change == "dependencies":
            entry = self.components[1]
            object.__setattr__(
                entry, "dependencies", tuple(list(entry.dependencies)),
            )
        else:
            object.__setattr__(
                self.components[0], "local_state", ReadinessState.BLOCKED,
            )

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", substituted)
    with pytest.raises(
        SyntheticStartupLeaseRejected, match="readiness inputs changed",
    ):
        _review(snapshot, requirement)
    assert calls == phase


def test_requirement_drift_between_integrity_passes_is_rejected(monkeypatch):
    snapshot, requirement = _state()
    original = StartupSnapshot._assert_integrity
    calls = 0

    def swapped_requirement(self):
        nonlocal calls
        original(self)
        calls += 1
        if calls == 1:
            object.__setattr__(requirement, "component_id", "scheduler")
            object.__setattr__(requirement, "schema_revision", "scheduler-v1")
        elif calls == 2:
            object.__setattr__(requirement, "component_id", "memory")
            object.__setattr__(requirement, "schema_revision", "memory-v1")

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", swapped_requirement)
    with pytest.raises(
        SyntheticStartupLeaseRejected, match="readiness inputs changed",
    ):
        _review(snapshot, requirement)
    assert calls == 1


def test_stable_lease_never_authorizes_startup_or_dispatch():
    snapshot, requirement = _state()
    receipt = _review(snapshot, requirement)
    assert receipt.required_components == ("memory",)
    assert receipt.startup_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.notification_authorized is False
