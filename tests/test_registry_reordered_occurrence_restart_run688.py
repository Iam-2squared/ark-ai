"""Cold restart reservation uniqueness is registry-order independent.

Only a synthetic local WRITE token and occurrence are reserved. Registry
reordering cannot create a second reservation or turn a local receipt into
permission for an external tool effect.
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


class _NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("reservation fixture invoked a real backend")


def _occurrence(text):
    return "occ_" + hashlib.sha256(text.encode("ascii")).hexdigest()


@pytest.mark.parametrize(
    "scenario",
    (
        "same_token_same_occurrence",
        "same_token_new_occurrence",
        "new_token_same_occurrence",
        "other_request_old_token",
        "expired_token",
        "noninteger_clock",
    ),
)
def test_reordered_registry_cannot_launder_reserved_write_after_restart(
    tmp_path, scenario,
):
    backend = _NeverDispatch()
    write = ToolRegistration(
        "offline.write", "mock.write", Effect.WRITE, "local-mock", backend,
    )
    read = ToolRegistration(
        "offline.read", "mock.read", Effect.READ, "local-mock", backend,
    )
    before_registry = ToolRegistry((write, read))
    after_registry = ToolRegistry((read, write))
    assert before_registry.revision == after_registry.revision

    call = ToolCall(
        "offline.write", "mock.write", "private", {"fixture": "first"},
    )
    original = OneShotAuthorization("durable-token", call.request_id, 1000)
    path = tmp_path / "reservations.sqlite"
    first = SyntheticOccurrenceStore(path)
    first_receipt = first.reserve_synthetic(
        before_registry, call, original,
        occurrence_id=_occurrence("first"), now_ms=10,
    )
    assert first_receipt.dispatch_authorized is False
    assert first_receipt.outcome_known is False
    assert first_receipt.automatic_replay_authorized is False

    different_token = OneShotAuthorization("other-token", call.request_id, 1000)
    attempt_call = call
    attempt_token = original
    attempt_occurrence = _occurrence("first")
    attempt_clock = 11
    if scenario == "same_token_new_occurrence":
        attempt_occurrence = _occurrence("second")
    elif scenario == "new_token_same_occurrence":
        attempt_token = different_token
    elif scenario == "other_request_old_token":
        attempt_call = ToolCall(
            "offline.write", "mock.write", "private", {"fixture": "second"},
        )
        attempt_occurrence = _occurrence("second")
    elif scenario == "expired_token":
        attempt_token = different_token
        attempt_occurrence = _occurrence("second")
        attempt_clock = 1000
    elif scenario == "noninteger_clock":
        attempt_token = different_token
        attempt_occurrence = _occurrence("second")
        attempt_clock = True

    restarted = SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected):
        restarted.reserve_synthetic(
            after_registry, attempt_call, attempt_token,
            occurrence_id=attempt_occurrence, now_ms=attempt_clock,
        )
    assert first.count_synthetic() == 1
    assert restarted.count_synthetic() == 1
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0
