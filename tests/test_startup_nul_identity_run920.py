"""Disconnected startup probe identities reject NUL and foreign hooks.

Synthetic readiness remains a local claim, never execution or source authority.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _component(field: str, value: object) -> StartupComponent:
    if field == "component_id":
        return StartupComponent(value)
    if field == "dependency":
        return StartupComponent("core", (value,))
    if field == "failure_code":
        return StartupComponent("core", failure_code=value)
    if field == "schema_revision":
        return StartupComponent("core", schema_revision=value)
    raise AssertionError("test field typo")


@pytest.mark.parametrize(
    "field",
    ("component_id", "dependency", "failure_code", "schema_revision"),
)
def test_nul_identity_denied_before_it_can_enter_readiness_digest(
    field: str,
) -> None:
    with pytest.raises(ValueError, match="NUL separator"):
        _component(field, "safe\\x00forged".replace("\\x00", "\x00"))


@pytest.mark.parametrize(
    "field",
    ("component_id", "dependency", "failure_code", "schema_revision"),
)
def test_foreign_carrier_cannot_execute_hash_or_equality_hooks(
    field: str,
) -> None:
    class UntrustedText(str):
        def __hash__(self):
            pytest.fail("untrusted readiness identity hash executed")

        def __eq__(self, _other):
            pytest.fail("untrusted readiness identity equality executed")

    with pytest.raises(ValueError, match="exact text"):
        _component(field, UntrustedText("core"))


def test_valid_disconnected_graph_stays_ready_without_authority() -> None:
    snapshot = evaluate_startup_readiness((
        StartupComponent("registry", schema_revision="1"),
        StartupComponent("memory", ("registry",), ReadinessState.READY),
    ))
    assert snapshot.state("registry") is ReadinessState.READY
    assert snapshot.state("memory") is ReadinessState.READY
