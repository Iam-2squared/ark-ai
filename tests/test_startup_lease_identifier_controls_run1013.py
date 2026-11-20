"""Startup lease requirements reject diagnostic-control identities before matching.

These synthetic checks do not establish machine readiness or execution authority.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
)


@pytest.mark.parametrize("field", ("component_id", "schema_revision"))
@pytest.mark.parametrize(
    ("raw", "message"),
    (
        ("mem\\nory", "ASCII control"),
        ("mem\\ttory", "ASCII control"),
        ("mem\\x7fory", "ASCII control"),
        ("mem\\u202eory", "Unicode formatting control"),
        ("mem\\u200bory", "Unicode formatting control"),
        ("mem\\u2028ory", "Unicode formatting control"),
        ("mem\\u00adory", "Unicode formatting control"),
    ),
)
def test_requirement_rejects_diagnostic_control_characters_before_matching(
    field: str, raw: str, message: str,
) -> None:
    values = {"component_id": "memory", "schema_revision": "memory-v1"}
    values[field] = raw
    requirement = SyntheticReadinessRequirement(**values)
    with pytest.raises(SyntheticStartupLeaseRejected, match=message):
        requirement.assert_shape()


def test_requirement_keeps_ordinary_utf8_identifiers() -> None:
    requirement = SyntheticReadinessRequirement("memory-記録", "schema-v1")
    assert requirement.assert_shape() is None
