"""Synthetic receipt class identity is pinned before any forged constructor.

All cases use disposable SQLite and never call the backend.
"""

import pytest

import ark.agency.durable_occurrence_review as module
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("backend must never execute")


class _CommitHook:
    def __init__(self, inner, callback):
        self.inner = inner
        self.callback = callback

    def commit(self):
        self.inner.commit()
        self.callback()

    def __getattr__(self, name):
        return getattr(self.inner, name)


def _case(tmp_path):
    backend = NeverDispatch()
    call = ToolCall("fixture.writer", "fixture.write", "synthetic", {"x": 1})
    registry = ToolRegistry((
        ToolRegistration("fixture.writer", "fixture.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("token-for-class-custody", call.request_id, 1000)
    ledger = module.SyntheticOccurrenceStore(tmp_path / "receipt-custody.sqlite")
    return ledger, registry, call, token, backend


def _reserve(case, suffix="a"):
    ledger, registry, call, token, _backend = case
    return ledger.reserve_synthetic(
        registry, call, token, occurrence_id="occ_" + suffix * 64, now_ms=10,
    )


@pytest.mark.parametrize("phase,expected_rows", (
    ("preinstalled", 0),
    ("token_hash", 0),
    ("after_commit", 1),
))
def test_counterfeit_class_cannot_construct_or_grant_replay(
    tmp_path, monkeypatch, phase, expected_rows,
):
    case = _case(tmp_path)
    ledger, _registry, _call, _token, backend = case
    original = module.SyntheticReservationReceipt
    constructed = []
    hash_callback_calls = []

    class Counterfeit:
        # Copied original False-valued properties must not authenticate a
        # forged constructor or mint permission for a WRITE.
        dispatch_authorized = vars(original)["dispatch_authorized"]
        outcome_known = vars(original)["outcome_known"]
        automatic_replay_authorized = vars(original)["automatic_replay_authorized"]

        def __init__(self, *_args):
            constructed.append("called")
            raise AssertionError("forged constructor must not execute")

    def tamper():
        monkeypatch.setattr(module, "SyntheticReservationReceipt", Counterfeit)

    if phase == "preinstalled":
        tamper()
    elif phase == "token_hash":
        real_sha = module.hashlib.sha256

        def hash_with_swap(payload=b""):
            hash_callback_calls.append(payload)
            if isinstance(payload, bytes) and payload.startswith(b"ARK-synthetic-v1\0"):
                tamper()
            return real_sha(payload)

        monkeypatch.setattr(module.hashlib, "sha256", hash_with_swap)
    else:
        connect = ledger._connect

        def connect_with_commit_hook(**kwargs):
            return _CommitHook(connect(**kwargs), tamper)

        monkeypatch.setattr(ledger, "_connect", connect_with_commit_hook)

    expected = (
        "digest implementation changed"
        if phase == "token_hash"
        else "synthetic receipt authority descriptor changed"
    )
    with pytest.raises(module.SyntheticReplayRejected, match=expected):
        _reserve(case)
    assert constructed == []
    if phase == "token_hash":
        assert hash_callback_calls == []
    monkeypatch.undo()
    assert ledger.count_synthetic() == expected_rows
    assert backend.calls == 0
    if phase == "after_commit":
        # Commit did succeed despite later refusal: replay stays forbidden.
        with pytest.raises(module.SyntheticReplayRejected, match="already reserved"):
            _reserve(case, suffix="b")
        assert ledger.count_synthetic() == 1


def test_normal_receipt_still_denies_all_authority(tmp_path):
    case = _case(tmp_path)
    receipt = _reserve(case)
    assert type(receipt) is module.SyntheticReservationReceipt
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert case[0].count_synthetic() == 1
    assert case[4].calls == 0
