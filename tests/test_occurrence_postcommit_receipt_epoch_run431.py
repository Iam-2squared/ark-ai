"""A synthetic reservation's post-COMMIT receipt cannot grant false evidence.

The only side effect is a disposable local SQLite reservation. The backend is
never called and the receipt is not consent, external-outcome proof, or replay
authority. Rejections after COMMIT preserve the durable one-shot token.
"""

from pathlib import Path

import pytest

import ark.agency.durable_occurrence_review as occurrence
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic reservation cannot call a backend")


def _fixture(tmp_path):
    backend = NoDispatch()
    call = ToolCall("writer", "offline.write", "synthetic", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("offline-token", call.request_id, 1000)
    store = occurrence.SyntheticOccurrenceStore(tmp_path / "occ.sqlite")
    return store, registry, call, token, backend


def _reserve(state, *, occurrence_id="occ_" + "a" * 64):
    store, registry, call, token, _backend = state
    return store.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence_id, now_ms=10,
    )


def _equal_new(value):
    new = ("!" + value)[1:]
    assert new == value and new is not value
    return new


@pytest.mark.parametrize("mutation", (
    "wrong_type",
    "wrong_request",
    "equal_bound_identity",
    "token_after_commit",
    "equal_source_path",
))
def test_receipt_constructor_fault_preserves_committed_reservation(
    tmp_path, monkeypatch, mutation,
):
    state = _fixture(tmp_path)
    store, _registry, _call, token, backend = state
    original_type = occurrence.SyntheticReservationReceipt
    original_token_id = token.token_id

    def injected_constructor(*args):
        if mutation == "wrong_type":
            return object()
        receipt = original_type(*args)
        if mutation == "wrong_request":
            object.__setattr__(receipt, "request_id", "act_" + "0" * 64)
        elif mutation == "equal_bound_identity":
            object.__setattr__(
                receipt, "bound_action_id", _equal_new(receipt.bound_action_id),
            )
        elif mutation == "token_after_commit":
            object.__setattr__(token, "token_id", "tampered-token")
        elif mutation == "equal_source_path":
            new_path = Path(str(store._path))
            assert new_path == store._path and new_path is not store._path
            store._path = new_path
        return receipt

    monkeypatch.setattr(
        occurrence, "SyntheticReservationReceipt", injected_constructor,
    )
    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="receipt identity changed|token changed|source changed",
    ):
        _reserve(state)
    monkeypatch.undo()
    # A post-COMMIT rejection does NOT make the one-shot token available.
    assert store.count_synthetic() == 1
    object.__setattr__(token, "token_id", original_token_id)
    with pytest.raises(occurrence.SyntheticReplayRejected, match="already reserved"):
        _reserve(state, occurrence_id="occ_" + "b" * 64)
    assert store.count_synthetic() == 1
    assert backend.calls == 0


def test_normal_committed_receipt_is_exact_and_inert(tmp_path):
    state = _fixture(tmp_path)
    receipt = _reserve(state)
    assert type(receipt) is occurrence.SyntheticReservationReceipt
    assert receipt.request_id == state[2].request_id
    assert receipt.occurrence_id == "occ_" + "a" * 64
    assert state[0].count_synthetic() == 1
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert state[4].calls == 0
