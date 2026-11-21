"""Synthetic reservation receipts reject executable class changes pre-access.

These are disposable SQLite reservations, not execution authorization.
In particular, rejection after COMMIT never restores a one-shot token.
"""

from __future__ import annotations

import pytest

import ark.agency.durable_occurrence_review as occurrence
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("no registered backend may be called")


class AfterCommit:
    def __init__(self, connection, callback):
        self.connection = connection
        self.callback = callback

    def commit(self):
        self.connection.commit()
        self.callback()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def _fixture(tmp_path):
    backend = NeverExecute()
    call = ToolCall("offline.writer", "offline.write", "local", {"dry_run": True})
    registry = ToolRegistry((
        ToolRegistration("offline.writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("inert-fixture-token", call.request_id, 1000)
    ledger = occurrence.SyntheticOccurrenceStore(tmp_path / "receipt-slots.sqlite")
    return ledger, registry, call, token, backend


def _reserve(case, suffix="a"):
    ledger, registry, call, token, _ = case
    return ledger.reserve_synthetic(
        registry, call, token, occurrence_id="occ_" + suffix * 64,
        now_ms=100,
    )


@pytest.mark.parametrize("target", (
    "occurrence_id", "registry_revision", "bound_action_id",
    "request_id", "reserved_at_ms", "__init__", "__getattribute__",
))
@pytest.mark.parametrize("phase", ("before", "after_commit"))
def test_receipt_slot_or_hook_substitution_never_executes_poison(
    tmp_path, monkeypatch, target, phase,
):
    case = _fixture(tmp_path)
    ledger, _, _, _, backend = case
    invoked = []
    receipt_class = occurrence.SyntheticReservationReceipt

    def poison(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("replaced receipt descriptor must not run")

    def install():
        if target in ("__init__", "__getattribute__"):
            monkeypatch.setattr(receipt_class, target, poison)
        else:
            monkeypatch.setattr(receipt_class, target, property(poison))

    if phase == "before":
        install()
    else:
        original_connect = ledger._connect

        def with_commit_hook(**kwargs):
            return AfterCommit(original_connect(**kwargs), install)

        monkeypatch.setattr(ledger, "_connect", with_commit_hook)

    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="receipt authority descriptor changed",
    ):
        _reserve(case)
    assert invoked == []
    monkeypatch.undo()
    assert ledger.count_synthetic() == (0 if phase == "before" else 1)
    assert backend.calls == 0
    if phase == "after_commit":
        with pytest.raises(occurrence.SyntheticReplayRejected, match="already reserved"):
            _reserve(case, suffix="b")
        assert ledger.count_synthetic() == 1
        assert backend.calls == 0


def test_unmodified_receipt_has_only_inert_denials(tmp_path):
    case = _fixture(tmp_path)
    report = _reserve(case)
    assert type(report) is occurrence.SyntheticReservationReceipt
    assert report.dispatch_authorized is False
    assert report.outcome_known is False
    assert report.automatic_replay_authorized is False
    assert case[0].count_synthetic() == 1
    assert case[4].calls == 0
