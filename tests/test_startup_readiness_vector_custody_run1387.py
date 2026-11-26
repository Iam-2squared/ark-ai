"""Run1387: startup readiness constructor vectors retain import-time identity."""

from __future__ import annotations

import pytest

import ark.startup_readiness_review as readiness


def test_startup_constructor_vectors_cannot_be_rebound_together_before_probe_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    getter_calls: list[bool] = []
    consumed: list[bool] = []

    def hostile_getter(_instance):
        getter_calls.append(True)
        raise AssertionError("replaced startup component descriptor executed")

    monkeypatch.setattr(
        readiness.StartupComponent,
        "component_id",
        property(hostile_getter),
    )
    for name in (
        "_STARTUP_CARRIER_TYPES",
        "_STARTUP_CARRIER_FIELDS",
        "_STARTUP_CARRIER_HOOKS",
        "_ORIGINAL_CARRIER_FIELDS",
        "_ORIGINAL_CARRIER_HOOKS",
    ):
        monkeypatch.setattr(readiness, name, ())

    def probes():
        consumed.append(True)
        yield readiness.StartupComponent(
            "memory",
            schema_revision="memory-v1",
        )

    with pytest.raises(ValueError, match="startup constructor authority changed"):
        readiness.evaluate_startup_readiness(probes())

    assert getter_calls == []
    assert consumed == []
