"""Disconnected startup requirement names reject embedded NUL separators.

These fixture-only checks do not grant a real startup, scheduler or action.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
)


@pytest.mark.parametrize("field", ("component_id", "schema_revision"))
@pytest.mark.parametrize("raw", ("\x00starter", "sta\x00rter", "starter\x00"))
def test_requirement_refuses_nul_before_probe_matching(
    field: str, raw: str,
) -> None:
    values = {"component_id": "starter", "schema_revision": "schema-v1"}
    values[field] = raw
    requirement = SyntheticReadinessRequirement(**values)
    with pytest.raises(SyntheticStartupLeaseRejected, match="invalid NUL"):
        requirement.assert_shape()


def test_unmodified_requirement_keeps_original_contract() -> None:
    requirement = SyntheticReadinessRequirement("starter", "schema-v1")
    assert requirement.assert_shape() is None
