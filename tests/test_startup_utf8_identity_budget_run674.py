"""UTF-8 byte-accurate startup identities are inert and bounded.

All probes are synthetic. READY is a local graph claim, never permission to
start tools, notify, read private Memory or trust caller-supplied time.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize(
    "field",
    ("component_id", "dependencies", "failure_code", "schema_revision"),
)
@pytest.mark.parametrize(
    "bad",
    ("é" * 129, "😀" * 65, "broken\ud800"),
    ids=("two-byte-overflow", "four-byte-overflow", "invalid-surrogate"),
)
def test_probe_rejects_noncanonical_utf8_before_snapshot(field, bad):
    kwargs = {"component_id": "core"}
    kwargs[field] = (bad,) if field == "dependencies" else bad
    with pytest.raises(ValueError, match="UTF-8|bounded exact text"):
        StartupComponent(**kwargs)


@pytest.mark.parametrize(
    "value",
    ("a" * 256, "あ" * 85 + "a", "😀" * 64),
    ids=("ascii-256", "mixed-256", "four-byte-256"),
)
def test_exact_256_utf8_bytes_are_valid_for_all_identity_fields(value):
    components = (
        StartupComponent(value, schema_revision=value, failure_code=value),
        StartupComponent("child", dependencies=(value,)),
    )
    result = evaluate_startup_readiness(components)
    assert result.state(value) is ReadinessState.READY
    assert result.state("child") is ReadinessState.READY
    assert result.components[0].effective_state is ReadinessState.READY
    assert result.components[0].component_id in ("child", value)


@pytest.mark.parametrize(
    "field, replacement",
    (
        ("component_id", "😀" * 65),
        ("dependencies", ("あ" * 86,)),
        ("failure_code", "bad\udfff"),
        ("schema_revision", "é" * 129),
    ),
)
def test_postinit_reflected_overbudget_probe_cannot_become_ready(field, replacement):
    probe = StartupComponent("core", schema_revision="v1")
    object.__setattr__(probe, field, replacement)
    with pytest.raises(ValueError, match="UTF-8|bounded exact text"):
        evaluate_startup_readiness((probe,))


@pytest.mark.parametrize(
    "field, replacement",
    (
        ("component_id", "😀" * 65),
        ("dependencies", ("é" * 129,)),
        ("failure_code", "broken\ud800"),
        ("schema_revision", "あ" * 86),
    ),
)
def test_reflected_snapshot_cannot_be_reused_as_ready(field, replacement):
    snapshot = evaluate_startup_readiness((
        StartupComponent("core", schema_revision="v1"),
    ))
    object.__setattr__(snapshot.components[0], field, replacement)
    with pytest.raises(ValueError):
        snapshot.state("core")
