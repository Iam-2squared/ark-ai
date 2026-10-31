"""Detached synthetic recovery archive input carrier custody at read boundaries."""

import pytest

import ark.agency.synthetic_recovery_archive_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_recovery_triage import review_synthetic_write_recovery


class NoBackend:
    def __init__(self):
        self.executions = 0

    def execute(self, _call):
        self.executions += 1
        raise AssertionError("recovery archive must not execute a ToolBackend")


def _archive(tmp_path):
    call = ToolCall("fixture", "mock.write", "offline", {"value": 7})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("step", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "ledger.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture", "mock.write", Effect.WRITE, "no", backend),
    ))
    review = review_synthetic_write_recovery(
        journal, ledger._path, audit, registry, call, step_id="step",
    )
    return module.archive_synthetic_recovery(review), backend


def test_digest_callback_replacing_equal_archive_bytes_denied(tmp_path, monkeypatch):
    anchor, backend = _archive(tmp_path)
    digest = module._digest
    old = anchor.canonical_json

    def change_during_digest(raw):
        result = digest(raw)
        object.__setattr__(anchor, "canonical_json", bytes(bytearray(old)))
        return result

    monkeypatch.setattr(module, "_digest", change_during_digest)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="epoch"):
        module._restore(anchor)
    assert backend.executions == 0


def test_json_decode_replacing_equal_digest_carrier_denied(tmp_path, monkeypatch):
    anchor, backend = _archive(tmp_path)
    loads = module.json.loads
    old = anchor.digest

    def change_during_decode(raw):
        result = loads(raw)
        clone = ("!" + old)[1:]
        assert clone == old and clone is not old
        object.__setattr__(anchor, "digest", clone)
        return result

    monkeypatch.setattr(module.json, "loads", change_during_decode)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="epoch"):
        module._restore(anchor)
    assert backend.executions == 0


def test_json_canonicalization_replacing_equal_bytes_denied(tmp_path, monkeypatch):
    anchor, backend = _archive(tmp_path)
    canonical = module._canonical
    old = anchor.canonical_json

    def change_after_canonicalization(value):
        result = canonical(value)
        object.__setattr__(anchor, "canonical_json", bytes(bytearray(old)))
        return result

    monkeypatch.setattr(module, "_canonical", change_after_canonicalization)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="epoch"):
        module._restore(anchor)
    assert backend.executions == 0


def test_nested_but_digest_matched_json_is_bounded_rejection(tmp_path, monkeypatch):
    _anchor, backend = _archive(tmp_path)
    raw = b"[" * 1500 + b"0" + b"]" * 1500
    forged = module.SyntheticRecoveryArchive(raw, module._digest(raw))
    # JSON implementations may reject the nesting as malformed shape or
    # raise a recursion error. Either outcome must remain fail-closed.
    with pytest.raises(module.SyntheticRecoveryArchiveRejected):
        module._restore(forged)

    def recursive_decoder(_raw):
        raise RecursionError("synthetic deeply nested JSON decoder")

    monkeypatch.setattr(module.json, "loads", recursive_decoder)
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="invalid recovery archive"):
        module._restore(forged)
    assert backend.executions == 0


def test_unchanged_archive_roundtrip_remains_inert(tmp_path):
    archive, backend = _archive(tmp_path)
    identity, _plan, _ledger, _audit, _link, occurrences, links = module._restore(archive)
    assert identity["step_id"] == "step"
    assert occurrences == ()
    assert links == ()
    assert archive.dispatch_authorized is False
    assert archive.automatic_replay_authorized is False
    assert archive.external_outcome_known is False
    assert backend.executions == 0
