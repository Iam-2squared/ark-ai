"""Run1179: complete Unicode Cf rejection in startup graph and lease IDs."""

from __future__ import annotations

import pytest

from ark import startup_readiness_lease_review as lease
from ark import startup_readiness_review as readiness

_FORMAT_CONTROLS = ("\u0600", "\ufff9", "\U000e0001")


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize(
    "field", ("component_id", "dependency", "failure_code", "schema_revision"),
)
def test_startup_component_rejects_every_unicode_cf(
    control: str, field: str,
) -> None:
    if field == "component_id":
        build = lambda: readiness.StartupComponent("component" + control)
    elif field == "dependency":
        build = lambda: readiness.StartupComponent(
            "child", dependencies=("parent" + control,),
        )
    elif field == "failure_code":
        build = lambda: readiness.StartupComponent(
            "component",
            local_state=readiness.ReadinessState.BLOCKED,
            failure_code="failure" + control,
        )
    else:
        build = lambda: readiness.StartupComponent(
            "component", schema_revision="schema" + control,
        )

    with pytest.raises(ValueError, match="Unicode formatting control"):
        build()


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize("field", ("component_id", "schema_revision"))
def test_startup_lease_requirement_rejects_every_unicode_cf(
    control: str, field: str,
) -> None:
    values = {"component_id": "memory", "schema_revision": "memory-v1"}
    values[field] += control
    requirement = lease.SyntheticReadinessRequirement(**values)

    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="Unicode formatting control",
    ):
        requirement.assert_shape()


def test_startup_readiness_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        readiness.unicodedata, "category", lambda _character: "Lo",
    )
    with pytest.raises(ValueError, match="category classifier changed"):
        readiness.StartupComponent("component")


def test_startup_lease_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lease.unicodedata, "category", lambda _character: "Lo",
    )
    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="category classifier changed",
    ):
        lease.SyntheticReadinessRequirement(
            "memory", "memory-v1",
        ).assert_shape()
