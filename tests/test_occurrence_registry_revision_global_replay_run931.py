"""Disconnected occurrence reservations survive registry revision changes.

The store is a fixture-only replay fence, not an authenticator of human
approval, a trusted clock, or an external exactly-once executor.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("synthetic reservation must not call backend")


def _registry(backend_id: str, backend: _NeverExecute) -> ToolRegistry:
    return ToolRegistry((
        ToolRegistration(
            "local.write", "local.private", Effect.WRITE, backend_id, backend,
        ),
    ))


@pytest.mark.parametrize(
    "conflict", ("same_token_different_occurrence", "same_occurrence_new_token")
)
def test_registry_change_cannot_clear_global_reservation_fence(
    tmp_path, conflict: str,
) -> None:
    backend = _NeverExecute()
    old = _registry("mock-v1", backend)
    changed = _registry("mock-v2", backend)
    call = ToolCall("local.write", "local.private", "local:test", {"test": 1})
    first_token = OneShotAuthorization("token-one", call.request_id, 1000)
    first_occ = "occ_" + hashlib.sha256(b"old-occurrence").hexdigest()
    store_path = tmp_path / "local-only.sqlite3"
    initial = SyntheticOccurrenceStore(store_path)
    receipt = initial.reserve_synthetic(
        old, call, first_token, occurrence_id=first_occ, now_ms=100,
    )
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert old.revision != changed.revision
    assert old.bind(call).bound_action_id != changed.bind(call).bound_action_id

    if conflict == "same_token_different_occurrence":
        next_token = first_token
        next_occ = "occ_" + hashlib.sha256(b"new-occurrence").hexdigest()
    else:
        next_token = OneShotAuthorization("token-two", call.request_id, 1000)
        next_occ = first_occ

    # A fresh store and registry instance cannot reinterpret a committed
    # synthetic token/occurrence as new authority across revision changes.
    restarted = SyntheticOccurrenceStore(store_path)
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        restarted.reserve_synthetic(
            changed, call, next_token, occurrence_id=next_occ, now_ms=101,
        )
    assert restarted.count_synthetic() == initial.count_synthetic() == 1
    assert backend.calls == 0
