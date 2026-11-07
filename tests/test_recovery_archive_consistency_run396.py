"""Reject self-consistent but semantically contradictory detached recovery archives.

All evidence is synthetic; no backend is called and no approval is inferred.
"""

import json

import pytest

import ark.agency.synthetic_recovery_archive_review as archive_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_recovery_triage import review_synthetic_write_recovery


class _InertBackend:
    def execute(self, call):
        raise AssertionError("offline recovery archive must never execute a tool")


def _baseline(tmp_path):
    call = ToolCall("offline", "fixture.write", "test", {"task": "synthetic"})
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("one", call),),
    )
    path = tmp_path / "reservation.sqlite"
    SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    registry = ToolRegistry((
        ToolRegistration(
            "offline", "fixture.write", Effect.WRITE, "disconnected", _InertBackend(),
        ),
    ))
    review = review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="one",
    )
    original = archive_module.archive_synthetic_recovery(review)
    return json.loads(original.canonical_json)


@pytest.mark.parametrize(
    ("fault", "diagnostic"),
    (
        ("pending_ambiguous", "archive ambiguity contradicts planner state"),
        ("running_not_ambiguous", "archive ambiguity contradicts planner state"),
        ("duplicate_occurrence", "archive occurrence references are malformed"),
        ("invalid_occurrence", "archive occurrence references are malformed"),
        ("duplicate_audit_link", "archive occurrence references are malformed"),
        ("orphan_audit_link", "archive occurrence references are malformed"),
        ("duplicate_audit_link_id", "archive occurrence references are malformed"),
    ),
)
def test_detached_archive_must_have_consistent_state_and_references(
    tmp_path, fault, diagnostic,
):
    payload = _baseline(tmp_path)
    occ_a = "occ_" + "a" * 64
    occ_b = "occ_" + "b" * 64
    if fault == "pending_ambiguous":
        payload["identity"]["ambiguous_write"] = True
    elif fault == "running_not_ambiguous":
        payload["identity"]["step_state"] = "running"
    elif fault == "duplicate_occurrence":
        payload["occurrences"] = [occ_a, occ_a]
    elif fault == "invalid_occurrence":
        payload["occurrences"] = ["occ_not_a_valid_digest"]
    else:
        payload["link"] = {
            "event_count": 2,
            "tail_hash": "slink_" + "1" * 64,
            "last_link_at_ms": 10,
        }
        payload["occurrences"] = [occ_a]
        if fault == "orphan_audit_link":
            payload["audit_links"] = [[occ_b, 7]]
        elif fault == "duplicate_audit_link":
            payload["audit_links"] = [[occ_a, 7], [occ_a, 8]]
        else:
            payload["occurrences"] = [occ_a, occ_b]
            payload["audit_links"] = [[occ_a, 7], [occ_b, 7]]
    raw = json.dumps(
        payload, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    repaired_digest = archive_module.SyntheticRecoveryArchive(
        raw, archive_module._digest(raw),
    )
    with pytest.raises(
        archive_module.SyntheticRecoveryArchiveRejected, match=diagnostic,
    ):
        archive_module._restore(repaired_digest)


def test_stable_empty_archive_still_has_no_live_authority(tmp_path):
    payload = _baseline(tmp_path)
    raw = archive_module._canonical(payload)
    archive = archive_module.SyntheticRecoveryArchive(
        raw, archive_module._digest(raw),
    )
    archive_module._restore(archive)
    assert not archive.dispatch_authorized
    assert not archive.automatic_replay_authorized
    assert not archive.external_outcome_known
