"""Disconnected READ bindings pin their own constructor and exact slot getters.

All fixtures are in-memory synthetic READ computations, not ToolBackend calls.
"""

import subprocess
import sys

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


@pytest.mark.parametrize("hook", ("__init__",))
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


def test_replaced_new_is_rejected_without_poisoning_other_tests() -> None:
    """CPython caches __new__ slots after pytest monkeypatch undo.

    Exercise this hostile constructor in a disposable interpreter so that its
    class-slot side effects cannot break unrelated tests in this process.
    """
    probe = """
from ark.agency import disconnected_fixture_binding as binding
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest, execute_disconnected_fixture_tool,
)
request = DisconnectedToolRequest('req_' + 'a' * 32, 'math.sum', '{"values":[1,2]}')
result = execute_disconnected_fixture_tool(request)
executed = []
def adversarial(*args, **kwargs):
    executed.append('new')
    raise AssertionError('forged constructor executed')
binding.DisconnectedFixtureBinding.__new__ = adversarial
try:
    binding.bind_disconnected_fixture_result(request, result)
except binding.DisconnectedFixtureBindingRejected as exc:
    assert 'constructed binding' in str(exc)
else:
    raise AssertionError('forged __new__ replacement was accepted')
assert executed == []
"""
    child = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert child.returncode == 0, child.stderr


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
