"""Registry/SQLite COMMIT-UNKNOWN integration is local, inert and fail-closed."""

from __future__ import annotations

import sqlite3

import pytest

import ark.agency.disconnected_registered_unknown_bridge as bridge
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import derive_registered_atomic_intent
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("backend must never execute during recovery")


def _fixture(tmp_path, *, effect=Effect.WRITE):
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", effect, "local", backend),
    ))
    call = ToolCall("writer", "fixture.write", "offline", {"secret": "not-for-repr"})
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "intent.sqlite")
    before = genesis_atomic_preaction_witness()
    occurrence = "occ_" + "a" * 64
    return registry, call, ledger, before, occurrence, backend


def _review(parts):
    registry, call, ledger, before, occurrence, _ = parts
    return bridge.review_registered_unknown_outcome(
        registry, call, ledger, before, occurrence_id=occurrence,
    )


def _inert(result, backend):
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.human_approval_authenticated is False
    assert result.external_effect_verified is False
    assert result.cross_store_atomicity_proven is False
    assert result.manual_review_required is True
    assert backend.calls == 0
    assert "not-for-repr" not in repr(result)


def test_empty_registry_identity_and_sqlite_epoch_are_not_permission(tmp_path):
    parts = _fixture(tmp_path)
    first = _review(parts)
    assert first == _review(parts)
    assert first.local_state == "UNCHANGED"
    assert first.before_count == first.observed_count == 0
    assert first.registry_revision == parts[0].revision
    assert first.bound_action_id == parts[0].bind(parts[1]).bound_action_id
    assert len(first.evidence_sha256) == 64
    _inert(first, parts[-1])


def test_local_commit_unknown_is_not_external_success_or_replay(tmp_path):
    parts = _fixture(tmp_path)
    claim = derive_registered_atomic_intent(
        parts[0], parts[1], occurrence_id=parts[4],
    )
    parts[2].reserve(claim, retained=parts[3])
    reviewed = _review(parts)
    assert reviewed.local_state == "LOCALLY_RECORDED"
    assert reviewed.observed_count == 1
    _inert(reviewed, parts[-1])


def test_preexisting_local_intent_is_still_manual_only(tmp_path):
    parts = _fixture(tmp_path)
    claim = derive_registered_atomic_intent(parts[0], parts[1], occurrence_id=parts[4])
    tip = parts[2].reserve(claim, retained=parts[3])
    revised = (*parts[:3], tip, *parts[4:])
    reviewed = _review(revised)
    assert reviewed.local_state == "PREEXISTING"
    assert reviewed.before_count == 1
    _inert(reviewed, parts[-1])


def test_unrelated_commit_does_not_create_registered_intent(tmp_path):
    parts = _fixture(tmp_path)
    other_occurrence = "occ_" + "b" * 64
    other = derive_registered_atomic_intent(
        parts[0], parts[1], occurrence_id=other_occurrence,
    )
    parts[2].reserve(other, retained=parts[3])
    reviewed = _review(parts)
    assert reviewed.local_state == "ADVANCED_OTHER"
    _inert(reviewed, parts[-1])


@pytest.mark.parametrize(
    "problem", ("read", "malformed", "fake-prefix", "wrong-bound", "bad-audit"),
)
def test_denies_unregistered_or_corrupt_evidence(tmp_path, problem):
    parts = _fixture(tmp_path, effect=Effect.READ if problem == "read" else Effect.WRITE)
    if problem == "malformed":
        parts = (*parts[:4], "occ_invalid", parts[-1])
    elif problem == "fake-prefix":
        from ark.agency.disconnected_atomic_preaction_ledger import AtomicPreactionWitness
        parts = (*parts[:3], AtomicPreactionWitness(0, "f" * 64), *parts[4:])
    elif problem in ("wrong-bound", "bad-audit"):
        claim = derive_registered_atomic_intent(parts[0], parts[1], occurrence_id=parts[4])
        parts[2].reserve(claim, retained=parts[3])
        with sqlite3.connect(tmp_path / "intent.sqlite") as conn:
            if problem == "wrong-bound":
                conn.execute("UPDATE intents SET bound_action_id=?", ("bound_" + "f" * 64,))
            else:
                conn.execute("DELETE FROM preaction_audit")
    with pytest.raises(bridge.RegisteredUnknownOutcomeRejected):
        _review(parts)
    assert parts[-1].calls == 0


@pytest.mark.parametrize("target", (
    "registry-helper", "unknown-helper", "result-denial", "hash-helper",
))
def test_substituted_protocol_denied_before_untrusted_callback(tmp_path, monkeypatch, target):
    parts = _fixture(tmp_path)
    called = []

    def forbidden(*_args, **_kwargs):
        called.append(target)
        raise AssertionError("forged dependency must not execute")

    with monkeypatch.context() as patch:
        if target == "registry-helper":
            patch.setattr(bridge.binding, "derive_registered_atomic_intent", forbidden)
        elif target == "unknown-helper":
            patch.setattr(bridge.unknown, "review_atomic_unknown_outcome", forbidden)
        elif target == "result-denial":
            patch.setattr(
                bridge.RegisteredUnknownOutcomeReview,
                "automatic_replay_authorized", property(forbidden),
            )
        else:
            patch.setattr(bridge.hashlib, "sha256", forbidden)
        with pytest.raises(
            bridge.RegisteredUnknownOutcomeRejected, match="protocol changed",
        ):
            _review(parts)
    assert called == []
    assert parts[-1].calls == 0
