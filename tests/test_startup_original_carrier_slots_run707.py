"""Startup probes and cached readiness cannot execute replaced slot getters.

Every class-level mutation runs in its own Python process to avoid leaving
CPython type-slot caches or other tests altered. All inputs are disconnected.
A synthetic READY result is never physical-device or backend attestation.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.startup_readiness_review as startup


@pytest.mark.parametrize(
    ("carrier", "field"),
    (
        ("StartupComponent", "component_id"),
        ("StartupComponent", "dependencies"),
        ("StartupComponent", "local_state"),
        ("StartupComponent", "failure_code"),
        ("StartupComponent", "schema_revision"),
        ("ComponentResult", "component_id"),
        ("ComponentResult", "dependencies"),
        ("ComponentResult", "local_state"),
        ("ComponentResult", "effective_state"),
        ("ComponentResult", "failure_code"),
        ("ComponentResult", "schema_revision"),
        ("StartupSnapshot", "components"),
        ("StartupSnapshot", "digest"),
        ("StartupComponent", "__getattribute__"),
        ("ComponentResult", "__getattribute__"),
        ("StartupSnapshot", "__getattribute__"),
    ),
)
def test_replaced_startup_carrier_field_never_runs_before_early_denial(
    carrier, field,
):
    script = textwrap.dedent(
        f"""
        import ark.startup_readiness_review as module

        probe = module.StartupComponent("memory")
        snapshot = module.evaluate_startup_readiness((probe,))
        calls = []
        def hostile(*args):
            calls.append(True)
            raise AssertionError("hostile carrier getter executed")

        klass = getattr(module, {carrier!r})
        name = {field!r}
        replacement = hostile if name == "__getattribute__" else property(hostile)
        setattr(klass, name, replacement)
        try:
            if klass is module.StartupComponent:
                module.evaluate_startup_readiness((probe,))
            else:
                # Call the original class method without accessing a hostile
                # snapshot instance lookup hook.
                module._STARTUP_SNAPSHOT_RESULT_TYPE._assert_integrity(snapshot)
        except ValueError as exc:
            assert "startup constructor authority changed" in str(exc), str(exc)
        else:
            raise AssertionError("modified carrier unexpectedly accepted")
        assert calls == [], "hostile descriptor was accessed"
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_unmodified_startup_carriers_keep_dependency_results_inert():
    snapshot = startup.evaluate_startup_readiness((
        startup.StartupComponent(
            "local-memory", local_state=startup.ReadinessState.BLOCKED,
        ),
        startup.StartupComponent("local-planner", ("local-memory",)),
    ))
    assert snapshot.state("local-memory") is startup.ReadinessState.BLOCKED
    assert (
        snapshot.state("local-planner")
        is startup.ReadinessState.DEPENDENCY_BLOCKED
    )
    assert snapshot.root_blockers("local-planner") == ("local-memory",)
