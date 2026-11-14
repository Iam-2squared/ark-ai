"""Parallel WRITE-token admission stays process-local and fail-closed.

No ToolBackend dispatch, real human authorization, durable token consumption,
or external exactly-once guarantee is implied by these thread fixtures.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

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
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("authorization review cannot dispatch")


@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("iteration", range(2))
def test_two_threads_racing_one_token_yield_exactly_one_admission(
    registered, iteration,
):
    gate = PermissionGate()
    backend = NoDispatch()
    call = ToolCall("offline", "synthetic.write", "private", {"try": iteration})
    spec = ToolSpec("offline", "synthetic.write", Effect.WRITE)
    registry = ToolRegistry((
        ToolRegistration(
            "offline", "synthetic.write", Effect.WRITE, "mock", backend,
        ),
    ))
    grant = CapabilityGrant("synthetic.write", "private", 500)
    token = OneShotAuthorization(
        "same-process-token", call.request_id, 500,
    )
    barrier = Barrier(2, timeout=15)

    def attempt(_):
        barrier.wait()
        try:
            if registered:
                result = gate.authorize_registered(
                    registry, call, (grant,), now_ms=10, one_shot=token,
                )
                assert result.call is call
            else:
                assert gate.authorize(
                    spec, call, (grant,), now_ms=10, one_shot=token,
                ) is None
        except PermissionDenied as error:
            return ("DENIED", str(error))
        return ("AUTHORIZED", "")

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(attempt, range(2)))
    assert [row[0] for row in responses].count("AUTHORIZED") == 1
    denied = [row[1] for row in responses if row[0] == "DENIED"]
    assert len(denied) == 1
    assert "already consumed" in denied[0]
    assert gate._consumed_tokens == {"same-process-token"}
    assert backend.calls == 0


@pytest.mark.parametrize("registered", (False, True))
def test_two_independent_gates_do_not_claim_durable_cross_gate_dedup(
    registered,
):
    backend = NoDispatch()
    call = ToolCall("offline", "synthetic.write", "private")
    spec = ToolSpec("offline", "synthetic.write", Effect.WRITE)
    registry = ToolRegistry((
        ToolRegistration(
            "offline", "synthetic.write", Effect.WRITE, "mock", backend,
        ),
    ))
    grant = CapabilityGrant("synthetic.write", "private")
    token = OneShotAuthorization("local-only", call.request_id, 500)
    gates = (PermissionGate(), PermissionGate())
    for gate in gates:
        if registered:
            result = gate.authorize_registered(
                registry, call, (grant,), now_ms=10, one_shot=token,
            )
            assert result.call is call
        else:
            gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
    assert all(gate._consumed_tokens == {"local-only"} for gate in gates)
    assert backend.calls == 0
    # The separate durable Occurrence store, not PermissionGate, must
    # reject duplicate reservations across restarts and processes.
