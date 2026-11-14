"""Read-only terminal archive review rejects reentrant final-read source drift.

All files/steps here are synthetic; no ToolBackend or external executor runs.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_batch_failure_archive as archive
from ark.agency.disconnected_batch_failure_fixture import (
    simulate_disconnected_failure_fixture,
)
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule


def _case(tmp_path):
    first = DisconnectedBatchStep(
        "step_" + "a" * 16, "math.sum", '{"values":[1,2]}',
    )
    second = DisconnectedBatchStep(
        "step_" + "b" * 16, "text.stats", '{"text":"fixture"}',
        (first.step_id,),
    )
    plan = build_disconnected_batch_plan(
        "req_" + "e" * 32, (first, second),
    )
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    failure_mask = (first.step_id,)
    fixture = simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failure_mask,
    )
    path = tmp_path / "terminal.json"
    archived = archive.archive_disconnected_failure_fixture(
        fixture, plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path,
    )
    return plan, schedule, failure_mask, path, archived


def _review(plan, schedule, mask, path, witness):
    return archive.review_disconnected_failure_archive(
        plan, schedule, retained_plan_digest=plan.plan_digest,
        retained_failed_step_ids=mask, path=path,
        retained_file_sha256=witness.file_sha256,
    )


def test_valid_terminal_witness_remains_detached_and_non_authorizing(tmp_path):
    plan, schedule, mask, path, witness = _case(tmp_path)
    observed = _review(plan, schedule, mask, path, witness)
    assert observed == witness
    assert observed.terminal_counts == (0, 1, 1)
    assert observed.external_dispatch_authorized is False
    assert observed.write_authorized is False
    assert observed.automatic_replay_authorized is False
    assert observed.failure_authenticated is False
    assert observed.real_outcome_proven is False


@pytest.mark.parametrize("mutation", (
    "counts", "file_digest", "equal_digest_carrier",
    "equal_failure_mask_carrier", "rebind_false_authority", "grant_authority",
))
def test_last_archive_file_read_cannot_retarget_final_receipt(
    tmp_path, monkeypatch, mutation,
):
    plan, schedule, mask, path, retained = _case(tmp_path)
    source_bytes = path.read_bytes()
    original_read = archive._read_once
    original_witness = archive._witness
    calls = [0]
    captured = []

    def capture_witness(sha256, receipt):
        report = original_witness(sha256, receipt)
        captured.extend((report, receipt))
        return report

    def reenter_at_final_read(candidate):
        result = original_read(candidate)
        calls[0] += 1
        if calls[0] == 3:
            report, receipt = captured
            if mutation == "counts":
                object.__setattr__(report, "terminal_counts", (2, 0, 0))
            elif mutation == "file_digest":
                object.__setattr__(report, "file_sha256", "0" * 64)
            elif mutation == "equal_digest_carrier":
                original = report.fixture_digest
                clone = ("!" + original)[1:]
                assert clone == original and clone is not original
                object.__setattr__(report, "fixture_digest", clone)
            elif mutation == "equal_failure_mask_carrier":
                original = receipt.failed_step_ids
                clone = tuple(list(original))
                assert clone == original and clone is not original
                object.__setattr__(receipt, "failed_step_ids", clone)
            elif mutation == "rebind_false_authority":
                monkeypatch.setattr(
                    archive.ArchivedDisconnectedFailure,
                    "external_dispatch_authorized", property(lambda self: False),
                )
            else:
                monkeypatch.setattr(
                    archive.ArchivedDisconnectedFailure,
                    "external_dispatch_authorized", property(lambda self: True),
                )
        return result

    monkeypatch.setattr(archive, "_witness", capture_witness)
    monkeypatch.setattr(archive, "_read_once", reenter_at_final_read)
    with pytest.raises(archive.DisconnectedFailureArchiveRejected):
        _review(plan, schedule, mask, path, retained)
    assert calls == [3]
    assert path.read_bytes() == source_bytes
