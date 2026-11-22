"""Run1101: exact PermissionGate ingress and process-local one-shot behavior.

Only synthetic ToolSpec, ToolCall, grants and tokens are used. No backend is
registered or executed; the token set is explicitly process-local.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PermissionGate,
    ToolCall,
    ToolSpec,
)


def _read() -> tuple[ToolSpec, ToolCall, CapabilityGrant]:
    spec = ToolSpec("reader", "fixture.read", Effect.READ)
    call = ToolCall("reader", "fixture.read", "local:scope", {"n": 1})
    grant = CapabilityGrant("fixture.read", "local:scope")
    return spec, call, grant


def _write() -> tuple[ToolSpec, ToolCall, CapabilityGrant, OneShotAuthorization]:
    spec = ToolSpec("writer", "fixture.write", Effect.WRITE)
    call = ToolCall("writer", "fixture.write", "local:scope", {"n": 1})
    grant = CapabilityGrant("fixture.write", "local:scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 1000)
    return spec, call, grant, token


def test_read_requires_active_exact_scope_grant_and_exact_clock() -> None:
    gate = PermissionGate()
    spec, call, grant = _read()

    gate.authorize(spec, call, (grant,), now_ms=10)
    with pytest.raises(PermissionDenied, match="no active exact-scope"):
        gate.authorize(
            spec, call, (CapabilityGrant("fixture.read", "other-scope"),),
            now_ms=10,
        )
    with pytest.raises(PermissionDenied, match="no active exact-scope"):
        gate.authorize(
            spec, call, (CapabilityGrant("fixture.read", "local:scope", 10),),
            now_ms=10,
        )
    with pytest.raises(ValueError, match="now_ms"):
        gate.authorize(spec, call, (grant,), now_ms=True)  # type: ignore[arg-type]
    assert gate._consumed_tokens == set()


def test_write_token_is_request_bound_expiry_checked_and_one_shot() -> None:
    gate = PermissionGate()
    spec, call, grant, token = _write()

    mismatch = OneShotAuthorization(
        "mismatched-token",
        ToolCall("writer", "fixture.write", "local:scope", {"n": 2}).request_id,
        1000,
    )
    with pytest.raises(PermissionDenied, match="does not match this request"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=mismatch)
    assert "mismatched-token" not in gate._consumed_tokens

    expired = OneShotAuthorization("expired-token", call.request_id, 10)
    with pytest.raises(PermissionDenied, match="expired"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=expired)
    assert "expired-token" not in gate._consumed_tokens

    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
    assert "synthetic-token" in gate._consumed_tokens
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)


def test_reentrant_grant_generator_cannot_mutate_an_admitted_grant_before_spend() -> None:
    gate = PermissionGate()
    spec, call, grant, token = _write()

    def hostile_grants():
        yield grant
        object.__setattr__(grant, "scope", "other:scope")
        yield CapabilityGrant("fixture.write", "local:scope")

    with pytest.raises(PermissionDenied, match="changed during grants"):
        gate.authorize(spec, call, hostile_grants(), now_ms=10, one_shot=token)
    assert "synthetic-token" not in gate._consumed_tokens


def test_concurrent_callers_can_consume_one_local_token_only_once() -> None:
    gate = PermissionGate()
    spec, call, grant, token = _write()
    barrier = Barrier(2)

    def attempt() -> bool:
        barrier.wait(timeout=10)
        try:
            gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
        except PermissionDenied:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _index: attempt(), range(2)))

    assert outcomes.count(True) == 1
    assert outcomes.count(False) == 1
    assert gate._consumed_tokens == {"synthetic-token"}


def test_permission_gate_subclass_cannot_replace_token_custody() -> None:
    spec, call, grant = _read()

    class ForeignGate(PermissionGate):
        pass

    with pytest.raises(PermissionDenied, match="exact PermissionGate"):
        ForeignGate().authorize(spec, call, (grant,), now_ms=10)
