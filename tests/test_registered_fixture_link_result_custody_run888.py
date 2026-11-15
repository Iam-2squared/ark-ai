"""Registered disconnected READ links cannot gain authority via class mutation.

Only synthetic in-memory math fixtures. No ToolBackend.execute invocation.
"""

import pytest

from ark.agency import disconnected_registered_fixture_join as join
from ark.agency.contracts import CapabilityGrant
from ark.agency.contracts import Effect
from ark.agency.contracts import ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration
from ark.agency.registry import ToolRegistry


class _NoDispatch:
    def execute(self, _call: ToolCall) -> object:
        raise AssertionError("registered backend execution is prohibited")


def _inputs() -> tuple[object, ...]:
    backend = _NoDispatch()
    registry = ToolRegistry((
        ToolRegistration(
            "math.sum", "fixture.read", Effect.READ, "disconnected", backend,
        ),
    ))
    gate = PermissionGate()
    call = ToolCall("math.sum", "fixture.read", "synthetic", {"values": [1, 2]})
    grants = (CapabilityGrant("fixture.read", "synthetic"),)
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    return registry, gate, call, grants, request, result, binding


def _join() -> join.RegisteredFixtureLink:
    registry, gate, call, grants, request, result, binding = _inputs()
    return join.review_registered_disconnected_fixture(
        registry, gate, call, grants, "step_" + "b" * 16,
        request, result, binding, observed_at_ms=100,
    )


@pytest.mark.parametrize("member", (
    "__init__", "link_sha256", "backend_dispatched", "write_authorized",
    "replay_authorized", "__getattribute__",
))
def test_reflected_link_member_is_rejected_before_replacement_executes(
    monkeypatch: pytest.MonkeyPatch, member: str,
) -> None:
    arguments = _inputs()
    executed: list[str] = []

    def hostile(*_args: object, **_kwargs: object) -> object:
        executed.append(member)
        raise AssertionError("hostile registered link callback executed")

    injected = hostile if member in {"__init__", "__getattribute__"} else property(hostile)
    monkeypatch.setattr(join.RegisteredFixtureLink, member, injected)
    with pytest.raises(
        join.RegisteredFixtureLinkRejected, match="result carrier changed",
    ):
        join.review_registered_disconnected_fixture(
            arguments[0], arguments[1], arguments[2], arguments[3],
            "step_" + "b" * 16, arguments[4], arguments[5], arguments[6],
            observed_at_ms=100,
        )
    assert executed == []


def test_reentrant_registered_preflight_cannot_swap_link_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arguments = _inputs()
    original = join.review_disconnected_registered_read
    executed: list[str] = []

    def hostile(*_args: object, **_kwargs: object) -> object:
        executed.append("constructor")
        raise AssertionError("hostile link constructor executed")

    def reenter(*args: object, **kwargs: object) -> object:
        result = original(*args, **kwargs)
        monkeypatch.setattr(join.RegisteredFixtureLink, "__init__", hostile)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(join, "review_disconnected_registered_read", reenter)
        with pytest.raises(
            join.RegisteredFixtureLinkRejected, match="result carrier changed",
        ):
            join.review_registered_disconnected_fixture(
                arguments[0], arguments[1], arguments[2], arguments[3],
                "step_" + "b" * 16, arguments[4], arguments[5], arguments[6],
                observed_at_ms=100,
            )
    assert executed == []


def test_normal_registered_fixture_link_is_never_tool_authority() -> None:
    linked = _join()
    assert linked.step_id == "step_" + "b" * 16
    assert len(linked.link_sha256) == 64
    assert linked.backend_dispatched is False
    assert linked.external_result_proven is False
    assert linked.write_authorized is False
    assert linked.replay_authorized is False
    assert linked.trusted_clock_or_consent_proven is False
