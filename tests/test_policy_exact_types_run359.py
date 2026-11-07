"""Disconnected, synthetic fail-closed authorization-carrier regression tests."""

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate


class _PretendGrant:
    capability = "files.write"
    scope = "workspace:synthetic"
    expires_at_ms = None


class _PretendOneShot:
    token_id = "fixture-token"
    expires_at_ms = 100

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id


@pytest.mark.parametrize("invalid", [object(), _PretendGrant()])
def test_read_rejects_imitation_grants(invalid: object) -> None:
    call = ToolCall("files.read", "files.read", "workspace:synthetic")
    spec = ToolSpec("files.read", "files.read")
    with pytest.raises(PermissionDenied, match="exact value"):
        PermissionGate().authorize(spec, call, [invalid], now_ms=10)


def test_invalid_late_grant_cannot_consume_write_token() -> None:
    gate = PermissionGate()
    call = ToolCall("files.write", "files.write", "workspace:synthetic")
    spec = ToolSpec("files.write", "files.write", Effect.WRITE)
    grant = CapabilityGrant("files.write", "workspace:synthetic")
    token = OneShotAuthorization("fixture-token", call.request_id, 100)
    with pytest.raises(PermissionDenied, match="exact value"):
        gate.authorize(spec, call, [grant, _PretendGrant()], now_ms=10, one_shot=token)
    gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)


def test_fake_one_shot_rejected_before_grant_iteration() -> None:
    gate = PermissionGate()
    call = ToolCall("files.write", "files.write", "workspace:synthetic")
    spec = ToolSpec("files.write", "files.write", Effect.WRITE)
    grant = CapabilityGrant("files.write", "workspace:synthetic")
    with pytest.raises(PermissionDenied, match="exact value"):
        gate.authorize(
            spec,
            call,
            [grant],
            now_ms=10,
            one_shot=_PretendOneShot(call.request_id),  # type: ignore[arg-type]
        )


def test_non_tool_spec_and_call_rejected() -> None:
    gate = PermissionGate()
    call = ToolCall("files.read", "files.read", "workspace:synthetic")
    spec = ToolSpec("files.read", "files.read")
    grant = CapabilityGrant("files.read", "workspace:synthetic")
    with pytest.raises(PermissionDenied, match="exact ToolSpec"):
        gate.authorize(object(), call, [grant], now_ms=10)  # type: ignore[arg-type]
    with pytest.raises(PermissionDenied, match="exact ToolSpec"):
        gate.authorize(spec, object(), [grant], now_ms=10)  # type: ignore[arg-type]


def test_normal_read_and_write_permissions_remain_available() -> None:
    gate = PermissionGate()
    read = ToolCall("files.read", "files.read", "workspace:synthetic")
    gate.authorize(
        ToolSpec("files.read", "files.read"),
        read,
        [CapabilityGrant("files.read", "workspace:synthetic")],
        now_ms=10,
    )
    write = ToolCall("files.write", "files.write", "workspace:synthetic")
    gate.authorize(
        ToolSpec("files.write", "files.write", Effect.WRITE),
        write,
        [CapabilityGrant("files.write", "workspace:synthetic")],
        now_ms=10,
        one_shot=OneShotAuthorization("tok-2", write.request_id, 100),
    )
