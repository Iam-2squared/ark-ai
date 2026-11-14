"""Disconnected cross-store recovery must reject transient input mutations.

A later read callback must never be allowed to restore an earlier unsafe
source, ToolCall, or independently retained-history substitution.
"""

from pathlib import Path

import pytest

import ark.agency.synthetic_recovery_triage as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("offline recovery cannot dispatch")


def _state(tmp_path: Path):
    call = ToolCall("synthetic", "mock", "local", {"value": 1})
    registry = ToolRegistry((
        ToolRegistration("synthetic", "mock", Effect.WRITE, "inert", NeverBackend()),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("only", call),),
    )
    reservations = tmp_path / "reservation.sqlite"
    SyntheticOccurrenceStore(reservations)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    return journal, reservations, audit, registry, call


def _review(state, **kwargs):
    journal, reservations, audit, registry, call = state
    return module.review_synthetic_write_recovery(
        journal, reservations, audit, registry, call, step_id="only", **kwargs,
    )


def _mutators(state, target, retained):
    journal, _reservations, audit, _registry, call = state
    if target == "call":
        original = call.scope

        def mutate():
            object.__setattr__(call, "scope", "different")

        def restore():
            object.__setattr__(call, "scope", original)

    elif target == "plan":
        original = retained.status_digest

        def mutate():
            object.__setattr__(retained, "status_digest", "pstate_" + "0" * 64)

        def restore():
            object.__setattr__(retained, "status_digest", original)

    elif target == "audit":
        original = retained.chain_sha256

        def mutate():
            object.__setattr__(retained, "chain_sha256", "0" * 64)

        def restore():
            object.__setattr__(retained, "chain_sha256", original)

    elif target == "journal_path":
        original = journal._path

        def mutate():
            journal._path = Path(str(original))

        def restore():
            journal._path = original

    else:
        original = audit.path

        def mutate():
            audit.path = Path(str(original))

        def restore():
            audit.path = original

    return mutate, restore


@pytest.mark.parametrize("target", ("call", "audit_path", "plan"))
def test_ledger_read_drift_cannot_be_restored_by_audit_callback(
    tmp_path, monkeypatch, target,
):
    state = _state(tmp_path)
    plan = state[0].recover().tail
    retained = plan if target == "plan" else None
    mutate, restore = _mutators(state, target, retained)
    original_digest = module._digest
    original_audit = module.review_audit_continuity
    changed = False
    restored = False

    def digest(label, values):
        nonlocal changed
        result = original_digest(label, values)
        if label == "ARK-ledger-v1":
            mutate()
            changed = True
        return result

    def audit(*args, **kwargs):
        nonlocal restored
        if changed:
            restored = True
            restore()
        return original_audit(*args, **kwargs)

    monkeypatch.setattr(module, "_digest", digest)
    monkeypatch.setattr(module, "review_audit_continuity", audit)
    with pytest.raises(module.SyntheticRecoveryRejected, match="input|witness"):
        _review(state, retained_plan=plan)
    assert changed and not restored


@pytest.mark.parametrize("target", ("call", "journal_path", "audit"))
def test_final_plan_recheck_drift_cannot_be_restored_by_ledger_read(
    tmp_path, monkeypatch, target,
):
    state = _state(tmp_path)
    historical_audit = module.review_audit_continuity(state[2])
    retained = historical_audit if target == "audit" else None
    mutate, restore = _mutators(state, target, retained)
    original_recover = SyntheticPlanJournal.recover
    original_ledger = module.read_synthetic_ledger_witness
    recover_count = 0
    restored = False

    def recover(self, *, retained=None):
        nonlocal recover_count
        result = original_recover(self, retained=retained)
        recover_count += 1
        if recover_count == 2:
            mutate()
        return result

    def ledger(*args, **kwargs):
        nonlocal restored
        if recover_count == 2:
            restored = True
            restore()
        return original_ledger(*args, **kwargs)

    monkeypatch.setattr(SyntheticPlanJournal, "recover", recover)
    monkeypatch.setattr(module, "read_synthetic_ledger_witness", ledger)
    with pytest.raises(module.SyntheticRecoveryRejected, match="input|witness"):
        _review(state, retained_audit=historical_audit)
    assert recover_count == 2 and not restored


def test_final_audit_recheck_drift_cannot_be_restored_by_registry(
    tmp_path, monkeypatch,
):
    state = _state(tmp_path)
    original_audit = module.review_audit_continuity
    original_bind = ToolRegistry.bind
    count = 0
    restored = False
    mutate, restore = _mutators(state, "call", None)

    def audit(*args, **kwargs):
        nonlocal count
        result = original_audit(*args, **kwargs)
        count += 1
        if count == 2:
            mutate()
        return result

    def bind(self, call):
        nonlocal restored
        if count >= 2:
            restored = True
            restore()
        return original_bind(self, call)

    monkeypatch.setattr(module, "review_audit_continuity", audit)
    monkeypatch.setattr(ToolRegistry, "bind", bind)
    with pytest.raises(module.SyntheticRecoveryRejected, match="input"):
        _review(state)
    assert count == 2 and not restored


def test_unchanged_cross_store_review_never_grants_execution(tmp_path):
    result = _review(_state(tmp_path))
    assert result.matching_occurrences == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
