"""Detached local recovery archives must reject retagged noncanonical identities.

Matching a recomputed local SHA-256 is not a signature, approval, trusted
clock, external execution receipt, or permission to retry a WRITE.
"""

import json

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
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("archive diagnostics cannot invoke tools")


def _anchor(tmp_path):
    call = ToolCall("fixture", "mock.write", "offline", {"n": 7})
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


def _forge(payload):
    data = module._canonical(payload)
    return module.SyntheticRecoveryArchive(data, module._digest(data))


@pytest.mark.parametrize(("field", "replacement"), (
    ("request_id", "act_" + "g" * 64),
    ("registry_revision", "tools_" + "G" * 64),
    ("bound_action_id", "bound_" + "f" * 63),
    ("request_id", "not-an-action"),
))
def test_retagged_invalid_action_identity_denied_before_reopen(
    tmp_path, field, replacement,
):
    original, backend = _anchor(tmp_path)
    payload = json.loads(original.canonical_json)
    payload["identity"][field] = replacement
    with pytest.raises(module.SyntheticRecoveryArchiveRejected, match="identity is malformed"):
        module._restore(_forge(payload))
    assert backend.calls == 0


@pytest.mark.parametrize("change", (
    "orphan_reference",
    "impossible_occurrence_count",
    "unsorted_occurrences",
))
def test_retagged_impossible_durable_reference_prefix_denied(
    tmp_path, change,
):
    original, backend = _anchor(tmp_path)
    payload = json.loads(original.canonical_json)
    one = "occ_" + "a" * 64
    two = "occ_" + "b" * 64
    if change == "orphan_reference":
        payload["audit_links"] = [[one, 1]]
    elif change == "impossible_occurrence_count":
        payload["occurrences"] = [one]
    else:
        payload["occurrences"] = [two, one]
    with pytest.raises(
        module.SyntheticRecoveryArchiveRejected,
        match="archive occurrence references are malformed",
    ):
        module._restore(_forge(payload))
    assert backend.calls == 0


def test_original_detached_archive_remains_inert_and_roundtrippable(tmp_path):
    original, backend = _anchor(tmp_path)
    decoded = module._restore(original)
    assert decoded[0]["step_id"] == "step"
    assert decoded[5] == ()
    assert decoded[6] == ()
    assert original.dispatch_authorized is False
    assert original.automatic_replay_authorized is False
    assert original.external_outcome_known is False
    assert backend.calls == 0
