"""Failure-aware hypothetical archives reject carrier swaps during callbacks."""

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


def fixture(tmp_path):
    first = DisconnectedBatchStep(
        "step_" + "1" * 16, "math.sum", '{"values":[1,2]}',
    )
    second = DisconnectedBatchStep(
        "step_" + "2" * 16, "text.stats", '{"text":"synthetic"}',
        (first.step_id,),
    )
    plan = build_disconnected_batch_plan("req_" + "e" * 32, (first, second))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    failures = (first.step_id,)
    receipt = simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failures,
    )
    path = tmp_path / "failure-fixture.json"
    witness = archive.archive_disconnected_failure_fixture(
        receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path,
    )
    return plan, schedule, failures, receipt, path, witness


def review(values):
    plan, schedule, failures, _, path, witness = values
    return archive.review_disconnected_failure_archive(
        plan, schedule, retained_plan_digest=plan.plan_digest,
        retained_failed_step_ids=failures, path=path,
        retained_file_sha256=witness.file_sha256,
    )


def equal_copy(value):
    result = (value + "x")[:-1]
    assert result == value and result is not value
    return result


@pytest.mark.parametrize("field", ("fixture_digest", "terminal_states"))
def test_final_read_cannot_replace_equal_valued_replayed_receipt(
    tmp_path, monkeypatch, field,
):
    values = fixture(tmp_path)
    original_sim = archive.simulate_disconnected_failure_fixture
    original_read = archive._read_once
    seen = []
    reads = 0

    def tracked_simulation(*args, **kwargs):
        result = original_sim(*args, **kwargs)
        seen.append(result)
        return result

    def reentrant_read(path):
        nonlocal reads
        result = original_read(path)
        reads += 1
        if reads == 3:
            target = seen[1]
            previous = getattr(target, field)
            replacement = (
                tuple(list(previous)) if field == "terminal_states"
                else equal_copy(previous)
            )
            assert replacement == previous and replacement is not previous
            object.__setattr__(target, field, replacement)
        return result

    monkeypatch.setattr(
        archive, "simulate_disconnected_failure_fixture", tracked_simulation,
    )
    monkeypatch.setattr(archive, "_read_once", reentrant_read)
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="changed"):
        review(values)
    assert reads == 3


def test_witness_denial_cannot_replace_equal_valued_source_receipt(
    tmp_path, monkeypatch,
):
    values = fixture(tmp_path)
    original = archive._witness
    seen = {}

    def track_witness(file_hash, receipt):
        seen["receipt"] = receipt
        return original(file_hash, receipt)

    def mutation_with_false(self):
        if "receipt" in seen:
            target = seen["receipt"]
            object.__setattr__(
                target, "fixture_digest", equal_copy(target.fixture_digest),
            )
        return False

    monkeypatch.setattr(archive, "_witness", track_witness)
    monkeypatch.setattr(
        archive.ArchivedDisconnectedFailure,
        "real_outcome_proven", property(mutation_with_false),
    )
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="changed"):
        review(values)


def test_verifier_equal_valued_receipt_swap_prevents_new_archive(
    tmp_path, monkeypatch,
):
    plan, schedule, _, receipt, _, _ = fixture(tmp_path)
    original = archive.verify_disconnected_failure_fixture

    def mutate_after_verify(candidate, *args, **kwargs):
        result = original(candidate, *args, **kwargs)
        object.__setattr__(
            candidate, "fixture_digest", equal_copy(candidate.fixture_digest),
        )
        return result

    monkeypatch.setattr(
        archive, "verify_disconnected_failure_fixture", mutate_after_verify,
    )
    path = tmp_path / "never-created.json"
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="changed"):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )
    assert not path.exists()


def test_untouched_failure_archive_remains_readonly_and_non_authorizing(tmp_path):
    values = fixture(tmp_path)
    outcome = review(values)
    assert outcome.file_sha256 == values[5].file_sha256
    assert outcome.terminal_counts == (0, 1, 1)
    assert outcome.failure_authenticated is False
    assert outcome.write_authorized is False
    assert outcome.real_outcome_proven is False
