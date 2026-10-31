"""Disconnected startup readiness must pin final constructor input and output.

No real probes, devices, backend execution or authenticated readiness state.
"""

import pytest

import ark.startup_readiness_review as startup


def _fixture():
    blocked = startup.StartupComponent(
        "storage", (), startup.ReadinessState.BLOCKED, "offline", "v1",
    )
    dependent = startup.StartupComponent(
        "planner", ("storage",), startup.ReadinessState.READY,
    )
    return blocked, dependent


@pytest.mark.parametrize(
    "target", ("component_id", "dependencies", "failure_code", "schema_revision"),
)
def test_constructor_cannot_retarget_original_probe(monkeypatch, target):
    blocked, dependent = _fixture()
    native_result = startup.StartupSnapshot

    def construct(*args):
        result = native_result(*args)
        if target == "component_id":
            object.__setattr__(blocked, "component_id", "other-storage")
        elif target == "dependencies":
            object.__setattr__(dependent, "dependencies", ("planner",))
        elif target == "failure_code":
            object.__setattr__(blocked, "failure_code", "retargeted")
        else:
            object.__setattr__(blocked, "schema_revision", "v2")
        return result

    monkeypatch.setattr(startup, "StartupSnapshot", construct)
    with pytest.raises(ValueError, match="startup input changed"):
        startup.evaluate_startup_readiness((blocked, dependent))


@pytest.mark.parametrize(
    "target", ("type", "components", "digest", "component_state", "component_id"),
)
def test_constructor_cannot_forge_detached_readiness(monkeypatch, target):
    blocked, dependent = _fixture()
    native_result = startup.StartupSnapshot

    def construct(*args):
        if target == "type":
            return object()
        result = native_result(*args)
        if target == "components":
            replacement = tuple(list(result.components))
            assert replacement == result.components
            assert replacement is not result.components
            object.__setattr__(result, "components", replacement)
        elif target == "digest":
            replacement = ("x" + result.digest)[1:]
            assert replacement == result.digest
            assert replacement is not result.digest
            object.__setattr__(result, "digest", replacement)
        elif target == "component_state":
            object.__setattr__(
                result.components[0], "effective_state",
                startup.ReadinessState.READY,
            )
        else:
            object.__setattr__(result.components[0], "component_id", "forged")
        return result

    monkeypatch.setattr(startup, "StartupSnapshot", construct)
    with pytest.raises(ValueError, match="startup result changed"):
        startup.evaluate_startup_readiness((blocked, dependent))


def test_untampered_result_keeps_blocked_dependencies():
    blocked, dependent = _fixture()
    first = startup.evaluate_startup_readiness((blocked, dependent))
    second = startup.evaluate_startup_readiness((blocked, dependent))
    assert first == second
    assert first.state("planner") is startup.ReadinessState.DEPENDENCY_BLOCKED
    assert first.root_blockers("planner") == ("storage",)
