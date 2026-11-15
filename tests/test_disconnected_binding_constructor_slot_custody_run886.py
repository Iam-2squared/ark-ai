"""Disconnected READ bindings pin their own constructor and exact slot getters.

All fixtures are in-memory synthetic READ computations, not ToolBackend calls.
"""

import pytest

from ark.agency import disconnected_fixture_binding as binding
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)


def _pair():
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    return request, execute_disconnected_fixture_tool(request)


@pytest.mark.parametrize("hook", ("__init__", "__new__"))
def test_replaced_exact_class_constructor_never_executes(
    monkeypatch: pytest.MonkeyPatch, hook: str,
) -> None:
    request, result = _pair()
    executed: list[str] = []

    def adversarial(*_args: object, **_kwargs: object) -> None:
        executed.append(hook)
        raise AssertionError("forged fixture binding constructor executed")

    monkeypatch.setattr(
        binding.DisconnectedFixtureBinding, hook,
        adversarial, raising=False,
    )
    with pytest.raises(
        binding.DisconnectedFixtureBindingRejected, match="constructed binding",
    ):
        binding.bind_disconnected_fixture_result(request, result)
    assert executed == []


@pytest.mark.parametrize("field", (
    "request_id", "operation", "input_digest", "result_digest",
    "request_bound_digest",
))
def test_replaced_binding_field_slot_never_runs_getter(
    monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    request, result = _pair()
    executed: list[str] = []

    def adversarial(_self: object) -> str:
        executed.append(field)
        raise AssertionError("forged receipt field getter executed")

    monkeypatch.setattr(
        binding.DisconnectedFixtureBinding, field, property(adversarial),
    )
    with pytest.raises(
        binding.DisconnectedFixtureBindingRejected, match="constructed binding",
    ):
        binding.bind_disconnected_fixture_result(request, result)
    assert executed == []


def test_normal_fixture_still_returns_non_authorizing_binding() -> None:
    request, result = _pair()
    receipt = binding.bind_disconnected_fixture_result(request, result)
    assert receipt.request_id == request.request_id
    assert len(receipt.request_bound_digest) == 64
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_verified is False
    assert receipt.automatic_replay_authorized is False
