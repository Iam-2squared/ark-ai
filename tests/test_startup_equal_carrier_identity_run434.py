"""A READY fixture cannot replace its original equal-valued ID carriers.

Only caller-supplied disconnected readiness graphs are tested. No real
hardware probe, credential, startup activation, or Tool dispatch occurs.
"""

import pytest

import ark.startup_readiness_review as module
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _distinct(value):
    other = ("!" + value)[1:]
    assert other == value and other is not value
    return other


def _graph():
    parent = StartupComponent(
        "alpha-readiness-root-12345", (),
        ReadinessState.BLOCKED,
        "offline-blocked-fixture-12345", "revision-fixture-12345",
    )
    child = StartupComponent(
        "zeta-downstream-fixture-12345", (parent.component_id,),
    )
    return parent, child


@pytest.mark.parametrize(
    "field", ("component_id", "failure_code", "schema_revision"),
)
def test_source_generator_equal_carrier_swap_is_rejected(field):
    parent, child = _graph()
    switched = []

    def probes():
        yield parent
        previous = getattr(parent, field)
        object.__setattr__(parent, field, _distinct(previous))
        switched.append(True)
        yield child

    with pytest.raises(ValueError, match="startup input changed"):
        evaluate_startup_readiness(probes())
    assert switched == [True]


@pytest.mark.parametrize(
    "field", ("component_id", "failure_code", "schema_revision"),
)
def test_cached_readiness_rejects_equal_identifier_drift_during_validation(
    monkeypatch, field,
):
    parent, child = _graph()
    snapshot = evaluate_startup_readiness((parent, child))
    root = next(
        entry for entry in snapshot.components
        if entry.component_id == parent.component_id
    )
    native = module._identifier
    injected = []

    def changed_identifier(value, label):
        checked = native(value, label)
        if not injected:
            previous = getattr(root, field)
            object.__setattr__(root, field, _distinct(previous))
            injected.append(True)
        return checked

    monkeypatch.setattr(module, "_identifier", changed_identifier)
    with pytest.raises(ValueError, match="startup snapshot identifier changed"):
        snapshot.state(parent.component_id)
    assert injected == [True]


def test_unmodified_readiness_still_quarantines_dependent_fixtures():
    parent, child = _graph()
    snapshot = evaluate_startup_readiness((parent, child))
    assert snapshot.state(parent.component_id) is ReadinessState.BLOCKED
    assert snapshot.state(child.component_id) is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers(child.component_id) == (parent.component_id,)
