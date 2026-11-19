"""Unicode diagnostic identity guards for disconnected startup snapshots.

These are synthetic readiness probes, never live service activation or evidence
of authentic clock, permission, model, or backend state.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)

# Explicitly target terminal controls, bidi display attacks and invisible keys.
_BAD = ("\u0085", "\u061c", "\u200b", "\u200e", "\u2028", "\u202e",
        "\u2060", "\u2066", "\ufeff")


@pytest.mark.parametrize("control", _BAD)
@pytest.mark.parametrize("field", (
    "component_id", "dependency", "failure_code", "schema_revision",
))
def test_startup_rejects_unicode_control_keys_at_constructor(control, field):
    bad = "left" + control + "right"
    fields = {"component_id": "trusted"}
    if field == "component_id":
        fields["component_id"] = bad
    elif field == "dependency":
        fields["dependencies"] = (bad,)
    else:
        fields[field] = bad
    with pytest.raises(ValueError, match="Unicode formatting control"):
        StartupComponent(**fields)


def test_mutated_probe_cannot_be_evaluated_as_ready():
    probe = StartupComponent("trusted")
    object.__setattr__(probe, "component_id", "trusted\u202espoof")
    with pytest.raises(ValueError, match="Unicode formatting control"):
        evaluate_startup_readiness((probe,))


def test_cached_snapshot_rejects_changed_spoofed_diagnostic():
    snapshot = evaluate_startup_readiness((StartupComponent("trusted"),))
    object.__setattr__(snapshot.components[0], "failure_code", "ok\u2066forged")
    with pytest.raises(ValueError, match="startup snapshot identifier changed"):
        snapshot._assert_integrity()


def test_legitimate_multilingual_probe_graph_remains_available():
    parent = StartupComponent("東京")
    child = StartupComponent(
        "בדיקה-شبكة", dependencies=("東京",),
        local_state=ReadinessState.DEGRADED,
        failure_code="مراجعة", schema_revision="版２",
    )
    snapshot = evaluate_startup_readiness((child, parent))
    assert tuple(item.component_id for item in snapshot.components) == (
        "בדיקה-شبكة", "東京",
    ) or set(item.component_id for item in snapshot.components) == {
        "בדיקה-شبكة", "東京",
    }
    snapshot._assert_integrity()
