"""Direct cross-store recovery must not inherit its caller's epoch fences."""

from pathlib import Path
from types import MappingProxyType

import pytest

import ark.agency.synthetic_recovery_triage as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_occurrence_continuity_review import (
    read_synthetic_ledger_witness,
)
from ark.agency.synthetic_recovery_triage import SyntheticRecoveryRejected


class NeverBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("offline recovery never dispatches")


def _fixture(tmp_path: Path):
    call = ToolCall("offline", "mock", "local", {"fixture": 1})
    registry = ToolRegistry((
        ToolRegistration("offline", "mock", Effect.WRITE, "inert", NeverBackend()),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    path = tmp_path / "reservations.sqlite"
    SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    links = SyntheticOccurrenceAuditLinkStore(tmp_path / "links.sqlite")
    return journal, path, audit, registry, call, links


def _review(state, **kwargs):
    journal, path, audit, registry, call, _links = state
    return module.review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="root", **kwargs,
    )


def test_stable_direct_review_never_grants_write(tmp_path: Path):
    state = _fixture(tmp_path)
    review = _review(state, link_store=state[5])
    assert review.matching_occurrences == ()
    assert review.ambiguous_write is False
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.external_outcome_known is False


@pytest.mark.parametrize("which", ["journal", "audit", "link"])
def test_same_string_source_object_replacement_during_direct_review(
    tmp_path: Path, monkeypatch, which: str,
):
    state = _fixture(tmp_path)
    original = module.review_audit_continuity

    def inject(*args, **kwargs):
        result = original(*args, **kwargs)
        if which == "journal":
            state[0]._path = Path(str(state[0]._path))
        elif which == "audit":
            state[2].path = Path(str(state[2].path))
        else:
            state[5]._path = Path(str(state[5]._path))
        return result

    monkeypatch.setattr(module, "review_audit_continuity", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="source changed|input"):
        _review(state, link_store=state[5])


def test_plan_topology_container_replacement_rejected(tmp_path: Path, monkeypatch):
    state = _fixture(tmp_path)
    original = SyntheticPlanJournal.recover

    def inject(self, *, retained=None):
        result = original(self, retained=retained)
        self._steps = tuple(list(self._steps))
        return result

    monkeypatch.setattr(SyntheticPlanJournal, "recover", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="input"):
        _review(state)


def test_equivalent_tool_arguments_mapping_replacement_rejected(tmp_path: Path, monkeypatch):
    state = _fixture(tmp_path)
    original = module.PlanGraph

    def inject(steps):
        graph = original(steps)
        call = state[4]
        object.__setattr__(call, "arguments", MappingProxyType(dict(call.arguments)))
        return graph

    monkeypatch.setattr(module, "PlanGraph", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="input"):
        _review(state)


@pytest.mark.parametrize("which", ["plan", "ledger", "audit"])
def test_retained_witness_rewrite_during_other_store_read_rejected(
    tmp_path: Path, monkeypatch, which: str,
):
    state = _fixture(tmp_path)
    retained = {
        "plan": state[0].recover().tail,
        "ledger": read_synthetic_ledger_witness(state[1]),
        "audit": module.review_audit_continuity(state[2]),
    }
    original = module.review_audit_continuity

    def inject(*args, **kwargs):
        result = original(*args, **kwargs)
        if which == "plan":
            object.__setattr__(retained["plan"], "status_digest", "state_" + "0" * 64)
        elif which == "ledger":
            object.__setattr__(
                retained["ledger"], "digest", "synthetic_ledger_" + "0" * 64,
            )
        else:
            object.__setattr__(retained["audit"], "chain_sha256", "0" * 64)
        return result

    monkeypatch.setattr(module, "review_audit_continuity", inject)
    with pytest.raises(SyntheticRecoveryRejected, match="witness|input"):
        _review(
            state, retained_plan=retained["plan"],
            retained_ledger=retained["ledger"], retained_audit=retained["audit"],
        )
