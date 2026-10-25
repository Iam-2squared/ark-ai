"""Disconnected occurrence admission fences around hash/SQLite callbacks.

All databases are disposable; no real approval issuer or backend exists.
"""

import hashlib
from types import MappingProxyType

import pytest

from ark.agency import durable_occurrence_review as occurrence
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def execute(self, _call):
        raise AssertionError("occurrence review cannot dispatch tools")


def _fixture(tmp_path):
    call = ToolCall("writer", "write", "local", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("writer", "write", Effect.WRITE, "mock", NoDispatch()),
    ))
    token = OneShotAuthorization("token-original", call.request_id, 1000)
    ledger = SyntheticOccurrenceStore(tmp_path / "ledger.sqlite")
    return ledger, registry, call, token


def _reserve(ledger, registry, call, token, occurrence_id="occ_" + "1" * 64):
    return ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence_id, now_ms=20,
    )


def _equal_arguments_replacement(call):
    object.__setattr__(
        call, "arguments", MappingProxyType(dict(call.arguments)),
    )


def test_token_id_mutated_during_digest_cannot_reserve(tmp_path, monkeypatch):
    ledger, registry, call, token = _fixture(tmp_path)
    real = hashlib.sha256

    def mutate_digest(payload=b""):
        if payload.startswith(b"ARK-synthetic-v1\\0"):
            object.__setattr__(token, "token_id", "token-retargeted")
        return real(payload)

    monkeypatch.setattr(occurrence.hashlib, "sha256", mutate_digest)
    with pytest.raises(SyntheticReplayRejected, match="input changed"):
        _reserve(ledger, registry, call, token)
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


def test_equal_arguments_carrier_changed_during_digest_cannot_reserve(
    tmp_path, monkeypatch,
):
    ledger, registry, call, token = _fixture(tmp_path)
    real = hashlib.sha256

    def mutate_digest(payload=b""):
        if payload.startswith(b"ARK-synthetic-v1\\0"):
            _equal_arguments_replacement(call)
        return real(payload)

    monkeypatch.setattr(occurrence.hashlib, "sha256", mutate_digest)
    with pytest.raises(SyntheticReplayRejected, match="input changed"):
        _reserve(ledger, registry, call, token)
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


def test_connection_opener_cannot_mutate_token_before_transaction(
    tmp_path, monkeypatch,
):
    ledger, registry, call, token = _fixture(tmp_path)
    original = ledger._connect

    def switched(*, create=False, pinned_path=None):
        conn = original(create=create, pinned_path=pinned_path)
        object.__setattr__(token, "token_id", "token-retargeted")
        return conn

    monkeypatch.setattr(ledger, "_connect", switched)
    with pytest.raises(SyntheticReplayRejected, match="input changed"):
        _reserve(ledger, registry, call, token)
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


class _ConnectionHook:
    def __init__(self, inner, on_begin=None, on_commit=None):
        self.inner = inner
        self.on_begin = on_begin
        self.on_commit = on_commit

    def execute(self, sql, *args, **kwargs):
        result = self.inner.execute(sql, *args, **kwargs)
        if sql == "BEGIN IMMEDIATE" and self.on_begin is not None:
            self.on_begin()
        return result

    def commit(self):
        self.inner.commit()
        if self.on_commit is not None:
            self.on_commit()

    def __getattr__(self, name):
        return getattr(self.inner, name)


def test_transaction_begin_cannot_retarget_equal_action(tmp_path, monkeypatch):
    ledger, registry, call, token = _fixture(tmp_path)
    original = ledger._connect
    monkeypatch.setattr(
        ledger, "_connect",
        lambda **kwargs: _ConnectionHook(
            original(**kwargs), on_begin=lambda: _equal_arguments_replacement(call),
        ),
    )
    with pytest.raises(SyntheticReplayRejected, match="input changed"):
        _reserve(ledger, registry, call, token)
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


def test_schema_check_cannot_retarget_equal_action(tmp_path, monkeypatch):
    ledger, registry, call, token = _fixture(tmp_path)
    real = occurrence._validate

    def retarget(conn):
        real(conn)
        _equal_arguments_replacement(call)

    monkeypatch.setattr(occurrence, "_validate", retarget)
    with pytest.raises(SyntheticReplayRejected, match="input changed"):
        _reserve(ledger, registry, call, token)
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


def test_post_commit_input_drift_is_failure_not_replay_authority(
    tmp_path, monkeypatch,
):
    ledger, registry, call, token = _fixture(tmp_path)
    original = ledger._connect
    monkeypatch.setattr(
        ledger, "_connect",
        lambda **kwargs: _ConnectionHook(
            original(**kwargs),
            on_commit=lambda: object.__setattr__(
                token, "token_id", "token-retargeted",
            ),
        ),
    )
    with pytest.raises(SyntheticReplayRejected, match="input changed"):
        _reserve(ledger, registry, call, token)
    monkeypatch.undo()
    assert ledger.count_synthetic() == 1
    object.__setattr__(token, "token_id", "token-original")
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        _reserve(ledger, registry, call, token, occurrence_id="occ_" + "2" * 64)


def test_normal_receipt_remains_inert(tmp_path):
    ledger, registry, call, token = _fixture(tmp_path)
    result = _reserve(ledger, registry, call, token)
    assert result.request_id == call.request_id
    assert ledger.count_synthetic() == 1
    assert result.dispatch_authorized is False
    assert result.outcome_known is False
    assert result.automatic_replay_authorized is False
