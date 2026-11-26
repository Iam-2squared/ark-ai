"""Registry-bound COMMIT-UNKNOWN: one local WAL epoch is never a retry grant."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_registered_unknown_bridge as bridge
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("offline recovery must never call the tool")


def _case(tmp_path):
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local:fixture", backend),
    ))
    call = ToolCall("writer", "fixture.write", "local:fixture", {"n": 1})
    path = tmp_path / "registered-unknown.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    return registry, call, ledger, backend


def _claim(registry, call, occurrence):
    return bridge.binding.derive_registered_atomic_intent(
        registry, call, occurrence_id=occurrence,
    )


def _review(registry, call, ledger, before, occurrence):
    return bridge.review_registered_unknown_outcome(
        registry, call, ledger, before, occurrence_id=occurrence,
    )


def _no_action(result, backend):
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.human_approval_authenticated is False
    assert result.external_effect_verified is False
    assert result.cross_store_atomicity_proven is False
    assert result.manual_review_required is True
    assert backend.calls == 0


@pytest.mark.parametrize(
    "case,expected,count",
    (
        ("empty", "UNCHANGED", 0),
        ("lost-receipt", "LOCALLY_RECORDED", 1),
        ("preexisting", "PREEXISTING", 1),
        ("unrelated-commit", "ADVANCED_OTHER", 1),
    ),
)
def test_registered_write_outcome_remains_manual_only(
    tmp_path, case, expected, count,
):
    registry, call, ledger, backend = _case(tmp_path)
    before = genesis_atomic_preaction_witness()
    occurrence = "occ_" + "a" * 64
    if case in ("lost-receipt", "preexisting"):
        written = ledger.reserve(_claim(registry, call, occurrence), retained=before)
        if case == "preexisting":
            before = written
    elif case == "unrelated-commit":
        ledger.reserve(
            _claim(registry, call, "occ_" + "b" * 64), retained=before,
        )
    result = _review(registry, call, ledger, before, occurrence)
    assert result.local_state == expected
    assert result.before_count == (1 if case == "preexisting" else 0)
    assert result.observed_count == count
    assert result.registry_revision == registry.revision
    assert len(result.evidence_sha256) == 64
    _no_action(result, backend)


def test_occurrence_collision_with_different_registry_bound_request_refused(tmp_path):
    registry, call, ledger, backend = _case(tmp_path)
    before = genesis_atomic_preaction_witness()
    occurrence = "occ_" + "a" * 64
    ledger.reserve(_claim(registry, call, occurrence), retained=before)
    different = ToolCall("writer", "fixture.write", "local:fixture", {"n": 2})
    with pytest.raises(
        bridge.RegisteredUnknownOutcomeRejected,
        match="registry-bound unknown evidence refused",
    ):
        _review(registry, different, ledger, before, occurrence)
    assert backend.calls == 0


@pytest.mark.parametrize("target", ("call-arguments", "before-tip", "registry-revision"))
def test_reentrant_registry_and_retained_epoch_drift_refused(
    tmp_path, monkeypatch, target,
):
    registry, call, ledger, backend = _case(tmp_path)
    before = genesis_atomic_preaction_witness()
    original_open = ledger._open

    def mutate_on_open(*, read_only):
        if target == "call-arguments":
            object.__setattr__(call, "arguments", {"n": 2})
        elif target == "before-tip":
            object.__setattr__(before, "tip_sha256", "f" * 64)
        else:
            # Simulate a forged registry revision carrier while opening the
            # independent SQLite epoch; it must not become a successful review.
            monkeypatch.setattr(registry, "_revision", "rev_" + "f" * 64)
        return original_open(read_only=read_only)

    monkeypatch.setattr(ledger, "_open", mutate_on_open)
    with pytest.raises(bridge.RegisteredUnknownOutcomeRejected):
        _review(registry, call, ledger, before, "occ_" + "a" * 64)
    assert backend.calls == 0


def test_preinstalled_result_denial_rebinding_rejected_before_lookup(
    tmp_path, monkeypatch,
):
    registry, call, ledger, backend = _case(tmp_path)
    seen = []

    def forbidden(_self):
        seen.append("called")
        raise AssertionError("untrusted denial callback must not execute")

    monkeypatch.setattr(
        bridge.RegisteredUnknownOutcomeReview,
        "automatic_replay_authorized", property(forbidden),
    )
    with pytest.raises(
        bridge.RegisteredUnknownOutcomeRejected, match="protocol changed",
    ):
        _review(
            registry, call, ledger, genesis_atomic_preaction_witness(),
            "occ_" + "a" * 64,
        )
    assert seen == []
    assert backend.calls == 0
