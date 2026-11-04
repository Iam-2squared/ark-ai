"""No mock reservation receipt can gain execution or replay authority.

Disposable SQLite only: no ToolBackend dispatch, external effects or issuer.
Preinstalled class rewrites are denied before reservation; post-COMMIT
substitutions cannot turn a consumed token into replay permission.
"""

import pytest

import ark.agency.durable_occurrence_review as occurrence
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic receipt must not dispatch")


def _setup(tmp_path):
    backend = NeverDispatch()
    call = ToolCall("fixture.writer", "fixture.write", "synthetic", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("fixture.writer", "fixture.write", Effect.WRITE, "mock", backend),
    ))
    store = occurrence.SyntheticOccurrenceStore(tmp_path / "receipt.sqlite")
    token = OneShotAuthorization("mock-token", call.request_id, 1000)
    return store, registry, call, token, backend


def _reserve(case, *, suffix="a"):
    store, registry, call, token, _ = case
    return store.reserve_synthetic(
        registry, call, token, occurrence_id="occ_" + suffix * 64, now_ms=10,
    )


class _AfterCommit:
    def __init__(self, inner, callback):
        self.inner = inner
        self.callback = callback

    def commit(self):
        self.inner.commit()
        self.callback()

    def __getattr__(self, name):
        return getattr(self.inner, name)


@pytest.mark.parametrize("property_name", (
    "dispatch_authorized", "outcome_known", "automatic_replay_authorized",
))
@pytest.mark.parametrize("replacement", (True, False))
def test_preinstalled_receipt_property_replacement_denied_before_spend(
    tmp_path, monkeypatch, property_name, replacement,
):
    case = _setup(tmp_path)
    monkeypatch.setattr(
        occurrence.SyntheticReservationReceipt,
        property_name, property(lambda self: replacement),
    )
    with pytest.raises(
        occurrence.SyntheticReplayRejected, match="receipt authority descriptor changed",
    ):
        _reserve(case)
    assert case[0].count_synthetic() == 0
    assert case[4].calls == 0


@pytest.mark.parametrize("property_name", (
    "dispatch_authorized", "outcome_known", "automatic_replay_authorized",
))
def test_postcommit_authority_rewrite_is_denied_before_getter(
    tmp_path, monkeypatch, property_name,
):
    case = _setup(tmp_path)
    ledger = case[0]
    original = occurrence.SyntheticReservationReceipt
    called = []

    def poisoned(_self):
        called.append(property_name)
        raise AssertionError("postcommit forged getter must not execute")

    connect = ledger._connect

    def with_postcommit_property_swap(**kwargs):
        return _AfterCommit(
            connect(**kwargs),
            lambda: monkeypatch.setattr(original, property_name, property(poisoned)),
        )

    monkeypatch.setattr(ledger, "_connect", with_postcommit_property_swap)
    with pytest.raises(
        occurrence.SyntheticReplayRejected, match="receipt authority descriptor changed",
    ):
        _reserve(case)
    assert called == []
    monkeypatch.undo()
    assert ledger.count_synthetic() == 1
    with pytest.raises(occurrence.SyntheticReplayRejected, match="already reserved"):
        _reserve(case, suffix="b")
    assert case[4].calls == 0


def test_ordinary_receipt_is_denial_only_and_single_use(tmp_path):
    case = _setup(tmp_path)
    receipt = _reserve(case)
    assert type(receipt) is occurrence.SyntheticReservationReceipt
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    with pytest.raises(occurrence.SyntheticReplayRejected, match="already reserved"):
        _reserve(case, suffix="b")
    assert case[4].calls == 0
