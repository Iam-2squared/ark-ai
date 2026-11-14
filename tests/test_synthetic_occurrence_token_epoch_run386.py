"""Synthetic token epochs must precede any caller-controlled registry callback.

This reservation fixture provides no consent issuer or ToolBackend execution.
"""

import hashlib
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("fixture may not dispatch")


def _inputs():
    registry = ToolRegistry(
        (ToolRegistration("mock", "write", Effect.WRITE, "local", NeverExecute()),)
    )
    call = ToolCall("mock", "write", "fixture", {"value": 1})
    token = OneShotAuthorization("original-token", call.request_id, 10_000)
    occurrence = "occ_" + hashlib.sha256(b"token-rebinding").hexdigest()
    return registry, call, token, occurrence


@pytest.mark.parametrize("field,replacement", [
    ("token_id", "replacement-token"),
    ("request_id", "act_" + "f" * 64),
    ("expires_at_ms", 11_000),
])
@pytest.mark.parametrize("during_bind", [1, 2])
def test_token_replacement_during_registry_bind_refuses_reservation(
    tmp_path: Path, monkeypatch, field, replacement, during_bind,
):
    path = tmp_path / "token-epoch.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call, token, occurrence = _inputs()
    original_bind = registry.bind
    calls = 0

    def reflect_token_after_bind(request):
        nonlocal calls
        calls += 1
        bound = original_bind(request)
        if calls == during_bind:
            object.__setattr__(token, field, replacement)
        return bound

    monkeypatch.setattr(registry, "bind", reflect_token_after_bind)
    with pytest.raises(SyntheticReplayRejected, match="token|action"):
        store.reserve_synthetic(
            registry, call, token, occurrence_id=occurrence, now_ms=10,
        )
    assert calls == during_bind
    assert SyntheticOccurrenceStore(path).count_synthetic() == 0


def test_unchanged_synthetic_token_is_one_shot_and_never_dispatches(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "token-epoch.sqlite")
    registry, call, token, occurrence = _inputs()
    receipt = store.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=10,
    )
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        store.reserve_synthetic(
            registry, call, token, occurrence_id=occurrence, now_ms=11,
        )
    assert store.count_synthetic() == 1
