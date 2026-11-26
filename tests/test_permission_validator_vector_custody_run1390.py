"""Run1390: PermissionGate retains grant, ToolSpec and token inventories."""

from __future__ import annotations

import pytest

import ark.agency.policy as policy
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate


def _write_fixture():
    call = ToolCall("writer", "fixture.write", "local:scope", {"n": 1})
    spec = ToolSpec("writer", "fixture.write", Effect.WRITE)
    grant = CapabilityGrant("fixture.write", "local:scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)
    return spec, call, grant, token


def test_joint_grant_vectors_are_rejected_before_grant_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, call, grant, token = _write_fixture()
    gate = PermissionGate()
    invoked: list[str] = []
    empty: tuple[object, ...] = ()
    monkeypatch.setattr(policy, "_GRANT_FIELDS", empty)
    monkeypatch.setattr(policy, "_ORIGINAL_GRANT_FIELDS", empty)
    monkeypatch.setattr(policy, "_GRANT_HOOKS", empty)
    monkeypatch.setattr(policy, "_ORIGINAL_GRANT_HOOKS", empty)
    monkeypatch.setattr(
        policy, "_GRANT_VECTOR_EPOCH", (empty, empty, empty, empty),
    )
    monkeypatch.setattr(
        CapabilityGrant,
        "capability",
        property(lambda _instance: (invoked.append("capability"), "fixture.write")[1]),
    )

    with pytest.raises(PermissionDenied, match="grant validator changed"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)

    assert invoked == []
    assert "synthetic-token" not in gate._consumed_tokens


def test_joint_spec_and_token_vectors_are_rejected_before_descriptors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, call, grant, token = _write_fixture()
    gate = PermissionGate()
    invoked: list[str] = []
    empty: tuple[object, ...] = ()
    for name in (
        "_SPEC_FIELDS", "_SPEC_METHODS", "_SPEC_HOOKS",
        "_ORIGINAL_SPEC_FIELDS", "_ORIGINAL_SPEC_METHODS", "_ORIGINAL_SPEC_HOOKS",
        "_TOKEN_FIELDS", "_TOKEN_METHODS", "_TOKEN_HOOKS",
        "_ORIGINAL_TOKEN_FIELDS", "_ORIGINAL_TOKEN_METHODS", "_ORIGINAL_TOKEN_HOOKS",
    ):
        monkeypatch.setattr(policy, name, empty)
    monkeypatch.setattr(
        policy, "_SPEC_TOKEN_VECTOR_EPOCH", tuple(empty for _ in range(12)),
    )
    monkeypatch.setattr(
        ToolSpec,
        "name",
        property(lambda _instance: (invoked.append("name"), "writer")[1]),
    )
    monkeypatch.setattr(
        OneShotAuthorization,
        "token_id",
        property(lambda _instance: (invoked.append("token_id"), "synthetic-token")[1]),
    )

    with pytest.raises(PermissionDenied, match="tool/token validator inventory changed"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)

    assert invoked == []
    assert "synthetic-token" not in gate._consumed_tokens
