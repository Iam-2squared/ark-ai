"""Concurrent in-process token spending is atomic, not durable authorization."""

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


def _fixture():
    gate = PermissionGate()
    spec = ToolSpec("file.write", "file.write", Effect.WRITE)
    call = ToolCall("file.write", "file.write", "local:fixture")
    grant = CapabilityGrant("file.write", "local:fixture")
    token = OneShotAuthorization("fixture-token", call.request_id, 100)
    return gate, spec, call, grant, token


def test_concurrent_same_token_allows_exactly_one_process_local_decision():
    gate, spec, call, grant, token = _fixture()
    barrier = Barrier(2)

    def authorize(_index: int) -> bool:
        barrier.wait(timeout=5)
        try:
            gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
        except PermissionDenied as exc:
            assert "already consumed" in str(exc)
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = list(pool.map(authorize, range(2)))
    assert sorted(decisions) == [False, True]
    assert gate._consumed_tokens == {token.token_id}


def test_different_tokens_can_each_be_spent_once():
    gate, spec, call, grant, _token = _fixture()

    def authorize(index: int) -> str:
        token = OneShotAuthorization(f"token-{index}", call.request_id, 100)
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
        return token.token_id

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(authorize, range(4)))
    assert set(results) == {f"token-{index}" for index in range(4)}


def test_invalid_request_does_not_spend_token():
    gate, spec, call, grant, _token = _fixture()
    bad = OneShotAuthorization("same-token", "act_" + "0" * 64, 100)
    with pytest.raises(PermissionDenied, match="does not match"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=bad)
    good = OneShotAuthorization("same-token", call.request_id, 100)
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=good)
    assert gate._consumed_tokens == {"same-token"}
