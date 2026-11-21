"""Disconnected occurrence reservations pin schema, bounds and ID parsers.

All examples are disposable local SQLite fixtures, never live PermissionGate
approval or ToolBackend execution. A committed reservation is not undone by
a later refusal, and no external-effect replay is authorized.
"""

from __future__ import annotations

import re

import pytest
from test_occurrence_input_commit_epoch_run410 import _fixture, _reserve

from ark.agency import durable_occurrence_review as occurrence

_MUTATIONS = (
    ("_TABLE", "CREATE TABLE unreviewed(x TEXT)"),
    ("_MAX", 2**63),
    ("_OCCURRENCE", re.compile(r"occ_.*")),
    ("_TOKEN_DIGEST", re.compile(r".*")),
    ("_REGISTRY_ID", re.compile(r".*")),
    ("_BOUND_ID", re.compile(r".*")),
    ("_REQUEST_ID", re.compile(r".*")),
)


@pytest.mark.parametrize(("name", "replacement"), _MUTATIONS)
@pytest.mark.parametrize("operation", ("initialize", "count", "reserve"))
def test_rebound_protocol_never_reads_or_reserves_private_fixture(
    tmp_path, monkeypatch, operation, name, replacement,
):
    ledger, registry, call, token = _fixture(tmp_path)
    fresh = tmp_path / "must-not-create.sqlite"
    monkeypatch.setattr(occurrence, name, replacement)
    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="synthetic occurrence protocol changed",
    ):
        if operation == "initialize":
            occurrence.SyntheticOccurrenceStore(fresh)
        elif operation == "count":
            ledger.count_synthetic()
        else:
            _reserve(ledger, registry, call, token)
    assert not fresh.exists()
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


def test_protocol_rebinding_after_registry_callback_refused_precommit(
    tmp_path, monkeypatch,
):
    ledger, registry, call, token = _fixture(tmp_path)
    original = type(registry).bind
    calls = []

    def mutate_after_bind(self, candidate):
        result = original(self, candidate)
        calls.append("bound without dispatch")
        monkeypatch.setattr(occurrence, "_MAX", 2**63)
        return result

    monkeypatch.setattr(type(registry), "bind", mutate_after_bind)
    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="synthetic occurrence protocol changed",
    ):
        _reserve(ledger, registry, call, token)
    assert calls == ["bound without dispatch"]
    monkeypatch.undo()
    assert ledger.count_synthetic() == 0


def test_protocol_change_after_commit_is_unknown_not_replay_permission(
    tmp_path, monkeypatch,
):
    ledger, registry, call, token = _fixture(tmp_path)
    real_connect = ledger._connect
    calls = []

    class CommitHook:
        def __init__(self, inner):
            self.inner = inner

        def commit(self):
            self.inner.commit()
            calls.append("durable fixture commit")
            monkeypatch.setattr(
                occurrence, "_TABLE", occurrence._TABLE + "\n-- unreviewed",
            )

        def __getattr__(self, name):
            return getattr(self.inner, name)

    monkeypatch.setattr(
        ledger, "_connect",
        lambda **kwargs: CommitHook(real_connect(**kwargs)),
    )
    with pytest.raises(
        occurrence.SyntheticReplayRejected,
        match="synthetic occurrence protocol changed",
    ):
        _reserve(ledger, registry, call, token)
    assert calls == ["durable fixture commit"]
    monkeypatch.undo()
    assert ledger.count_synthetic() == 1
    with pytest.raises(occurrence.SyntheticReplayRejected, match="already reserved"):
        _reserve(
            ledger, registry, call, token,
            occurrence_id="occ_" + "2" * 64,
        )
