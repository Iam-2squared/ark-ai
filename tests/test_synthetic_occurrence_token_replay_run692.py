"""Offline occurrence tokens and IDs stay one-shot across SQLite reopen.

This is a reservation ledger regression only: fixture tokens have no
authenticated issuer, clocks have no trusted authority, and no actual WRITE
backend is called or made retry-safe.
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
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("fixture reservation must not dispatch")


def _occurrence(seed):
    return "occ_" + hashlib.sha256(seed.encode("ascii")).hexdigest()


@pytest.mark.parametrize(
    "fault",
    (
        "same_token_new_occurrence",
        "new_token_same_occurrence",
        "cross_action_same_token",
        "cross_action_same_occurrence",
        "regressed_clock",
        "expired_token",
    ),
)
def test_cold_reopened_reservation_denies_replay_or_regression(
    tmp_path, fault,
):
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("mock.write", "fixture.write", Effect.WRITE, "local", backend),
    ))
    first_call = ToolCall(
        "mock.write", "fixture.write", "private", {"fixture": "first"},
    )
    other_call = ToolCall(
        "mock.write", "fixture.write", "private", {"fixture": "second"},
    )
    path = tmp_path / "reservations.sqlite"
    store = SyntheticOccurrenceStore(path)
    first = store.reserve_synthetic(
        registry, first_call,
        OneShotAuthorization("first-token", first_call.request_id, 1000),
        occurrence_id=_occurrence("first"), now_ms=10,
    )
    assert first.dispatch_authorized is False
    assert first.outcome_known is False
    assert first.automatic_replay_authorized is False

    target = other_call if fault.startswith("cross_action") else first_call
    token_id = (
        "first-token"
        if fault in ("same_token_new_occurrence", "cross_action_same_token")
        else "second-token"
    )
    occurrence = (
        _occurrence("first")
        if fault in ("new_token_same_occurrence", "cross_action_same_occurrence")
        else _occurrence("second")
    )
    now = 9 if fault == "regressed_clock" else 11
    expiry = 10 if fault == "expired_token" else 1000
    with pytest.raises(SyntheticReplayRejected):
        SyntheticOccurrenceStore(path).reserve_synthetic(
            registry, target,
            OneShotAuthorization(token_id, target.request_id, expiry),
            occurrence_id=occurrence, now_ms=now,
        )
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert backend.calls == 0

    # A fresh, independent occurrence can still reserve without reviving any
    # rejected token or claiming external exactly-once execution.
    fresh = SyntheticOccurrenceStore(path).reserve_synthetic(
        registry, other_call,
        OneShotAuthorization("unique-third-token", other_call.request_id, 1000),
        occurrence_id=_occurrence("third"), now_ms=12,
    )
    assert fresh.dispatch_authorized is False
    assert fresh.outcome_known is False
    assert fresh.automatic_replay_authorized is False
    assert SyntheticOccurrenceStore(path).count_synthetic() == 2
    assert backend.calls == 0
