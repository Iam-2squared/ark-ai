"""A detached fixture cycle archive cannot change during its final read callback."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_batch_cycle_archive as archive
from ark.agency.disconnected_batch_fixture_cycle import (
    simulate_disconnected_batch_fixture_cycle,
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
        "step_" + "2" * 16, "text.stats", '{"text":"fixture only"}',
        (first.step_id,),
    )
    plan = build_disconnected_batch_plan("req_" + "c" * 32, (first, second))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    receipt = simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=plan.plan_digest,
    )
    path = tmp_path / "detached-cycle.json"
    witness = archive.archive_disconnected_batch_fixture_cycle(
        receipt, plan, schedule,
        retained_plan_digest=plan.plan_digest, path=path,
    )
    return plan, schedule, receipt, path, witness


def review(plan, schedule, path, witness):
    return archive.review_disconnected_batch_fixture_cycle_archive(
        plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path, retained_file_sha256=witness.file_sha256,
    )


def equal_new_string(value):
    replacement = (value + "x")[:-1]
    assert replacement == value
    assert replacement is not value
    return replacement


@pytest.mark.parametrize("mutation", ("witness", "expected", "again", "descriptor"))
def test_final_archive_read_cannot_replace_checked_carriers(
    tmp_path, monkeypatch, mutation,
):
    plan, schedule, _, path, saved = fixture(tmp_path)
    seen = {"receipts": []}
    real_simulate = archive.simulate_disconnected_batch_fixture_cycle
    real_result = archive._result
    real_read = archive._read_once

    def track_simulation(*args, **kwargs):
        output = real_simulate(*args, **kwargs)
        seen["receipts"].append(output)
        return output

    def track_result(*args, **kwargs):
        output = real_result(*args, **kwargs)
        seen["witness"] = output
        return output

    count = 0

    def reentrant_read(candidate):
        nonlocal count
        observed = real_read(candidate)
        count += 1
        if count == 3:
            if mutation == "witness":
                target = seen["witness"]
                object.__setattr__(
                    target, "cycle_digest", equal_new_string(target.cycle_digest),
                )
            elif mutation in ("expected", "again"):
                target = seen["receipts"][0 if mutation == "expected" else 1]
                object.__setattr__(
                    target, "cycle_digest", equal_new_string(target.cycle_digest),
                )
            else:
                monkeypatch.setattr(
                    archive.ArchivedDisconnectedBatchCycle,
                    "write_authorized", property(lambda self: False),
                )
        return observed

    monkeypatch.setattr(
        archive, "simulate_disconnected_batch_fixture_cycle", track_simulation,
    )
    monkeypatch.setattr(archive, "_result", track_result)
    monkeypatch.setattr(archive, "_read_once", reentrant_read)
    with pytest.raises(archive.DisconnectedBatchArchiveRejected, match="final"):
        review(plan, schedule, path, saved)
    assert count == 3


def test_verifier_cannot_replace_receipt_with_equal_carriers_before_create(
    tmp_path, monkeypatch,
):
    plan, schedule, receipt, _, _ = fixture(tmp_path)
    real_verify = archive.verify_disconnected_batch_fixture_cycle

    def mutate_after_verify(original, *args, **kwargs):
        result = real_verify(original, *args, **kwargs)
        object.__setattr__(
            original, "cycle_digest", equal_new_string(original.cycle_digest),
        )
        return result

    monkeypatch.setattr(
        archive, "verify_disconnected_batch_fixture_cycle", mutate_after_verify,
    )
    candidate = tmp_path / "must-not-create.json"
    with pytest.raises(archive.DisconnectedBatchArchiveRejected, match="changed"):
        archive.archive_disconnected_batch_fixture_cycle(
            receipt, plan, schedule,
            retained_plan_digest=plan.plan_digest, path=candidate,
        )
    assert not candidate.exists()


def test_unchanged_archive_still_roundtrips_without_any_authority(tmp_path):
    plan, schedule, _, path, saved = fixture(tmp_path)
    result = review(plan, schedule, path, saved)
    assert result.file_sha256 == saved.file_sha256
    assert result.cycle_digest == saved.cycle_digest
    assert result.external_dispatch_authorized is False
    assert result.write_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.real_outcome_proven is False
