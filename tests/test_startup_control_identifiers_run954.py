"""Diagnostic-safe startup identities: no multiline or control spoofing."""

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize("control", ("\n", "\r", "\t", "\x1f", "\x7f"))
@pytest.mark.parametrize(
    "field",
    ("component_id", "dependency", "failure_code", "schema_revision"),
)
def test_startup_identifiers_reject_ascii_controls(field: str, control: str) -> None:
    fields = {
        "component_id": "local:memory",
        "dependencies": ("local:storage",),
        "failure_code": "PROBE_UNAVAILABLE",
        "schema_revision": "v1",
    }
    if field == "dependency":
        fields["dependencies"] = ("local:" + control + "storage",)
    else:
        fields[field] = "prefix" + control + "suffix"
    with pytest.raises(ValueError, match="ASCII control character"):
        StartupComponent(**fields)


@pytest.mark.parametrize("field", ("component_id", "failure_code", "schema_revision"))
def test_reflected_control_characters_cannot_become_ready_snapshot(field: str) -> None:
    probe = StartupComponent(
        "local:memory",
        local_state=ReadinessState.READY,
        failure_code="READY_ASSERTED",
        schema_revision="synthetic-v1",
    )
    object.__setattr__(probe, field, "synthetic\nforged:READY")
    with pytest.raises(ValueError, match="ASCII control character"):
        evaluate_startup_readiness((probe,))


def test_utf8_readiness_identity_keeps_dependency_denial() -> None:
    parent = StartupComponent("保存領域", local_state=ReadinessState.BLOCKED)
    child = StartupComponent("記憶検索", dependencies=("保存領域",))
    snapshot = evaluate_startup_readiness((child, parent))
    assert snapshot.state("保存領域") is ReadinessState.BLOCKED
    assert snapshot.state("記憶検索") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.digest.startswith("startup_")
