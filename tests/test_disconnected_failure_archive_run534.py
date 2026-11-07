"""Create-only terminal archive verifies failed/blocked fixture after restart."""

from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

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

REQ = "req_" + "b" * 32


def _fixture():
    first = DisconnectedBatchStep(
        "step_" + "1" * 16, "math.sum", '{"values":[1,2]}',
    )
    second = DisconnectedBatchStep(
        "step_" + "2" * 16, "text.stats", '{"text":"private synthetic phrase"}',
    )
    third = DisconnectedBatchStep(
        "step_" + "3" * 16, "text.find",
        '{"needle":"x","text":"xyz"}', (first.step_id, second.step_id),
    )
    plan = build_disconnected_batch_plan(REQ, (first, second, third))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    failures = (first.step_id,)
    receipt = simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=failures,
    )
    return plan, schedule, failures, receipt


def _write(tmp_path):
    plan, schedule, failures, receipt = _fixture()
    path = tmp_path / "synthetic-terminal.json"
    witness = archive.archive_disconnected_failure_fixture(
        receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path,
    )
    return plan, schedule, failures, receipt, path, witness


def _review(plan, schedule, failures, path, sha):
    return archive.review_disconnected_failure_archive(
        plan, schedule, retained_plan_digest=plan.plan_digest,
        retained_failed_step_ids=failures, path=path, retained_file_sha256=sha,
    )


def test_failure_propagation_roundtrip_restart_is_nonexecuting(tmp_path):
    plan, schedule, failures, receipt, path, witness = _write(tmp_path)
    assert receipt.terminal_states == (
        ("step_" + "1" * 16, "FAILED"),
        ("step_" + "2" * 16, "SUCCEEDED"),
        ("step_" + "3" * 16, "BLOCKED"),
    )
    assert witness.terminal_counts == (1, 1, 1)
    restarted_plan, restarted_schedule, _, _ = _fixture()
    assert restarted_plan is not plan
    restored = _review(
        restarted_plan, restarted_schedule, failures, path, witness.file_sha256,
    )
    assert restored == witness
    assert b"private synthetic phrase" not in path.read_bytes()
    assert restored.external_dispatch_authorized is False
    assert restored.write_authorized is False
    assert restored.automatic_replay_authorized is False
    assert restored.failure_authenticated is False
    assert restored.real_outcome_proven is False


def test_no_failure_mask_remains_hypothetical_even_if_all_succeed(tmp_path):
    plan, schedule, _, _ = _fixture()
    receipt = simulate_disconnected_failure_fixture(
        plan, schedule, retained_digest=plan.plan_digest,
        failed_step_ids=(),
    )
    path = tmp_path / "all-success-fixture.json"
    witness = archive.archive_disconnected_failure_fixture(
        receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path,
    )
    assert witness.terminal_counts == (3, 0, 0)
    assert _review(plan, schedule, (), path, witness.file_sha256) == witness
    assert witness.real_outcome_proven is False


@pytest.mark.parametrize("kind", (
    "tampered", "wrong_sha", "wrong_failure_mask", "extra_field", "empty",
))
def test_retained_fixture_and_archive_drift_are_rejected(tmp_path, kind):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    sha = witness.file_sha256
    if kind == "tampered":
        raw = path.read_bytes()
        path.write_bytes(b"X" + raw[1:])
    elif kind == "wrong_sha":
        sha = "0" * 64 if sha != "0" * 64 else "f" * 64
    elif kind == "wrong_failure_mask":
        failures = ()
    elif kind == "extra_field":
        raw = path.read_bytes()
        path.write_bytes(raw[:-1] + b',"unexpected":true}')
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        path.write_bytes(b"")
    with pytest.raises(archive.DisconnectedFailureArchiveRejected):
        _review(plan, schedule, failures, path, sha)


def test_preexisting_file_is_never_overwritten(tmp_path):
    plan, schedule, _, receipt = _fixture()
    path = tmp_path / "existing.json"
    path.write_bytes(b"owner's existing data")
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="create-only"):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )
    assert path.read_bytes() == b"owner's existing data"


@pytest.mark.parametrize("kind", ("relative", "dotdot", "missing_parent", "directory"))
def test_invalid_archive_paths_fail_closed(tmp_path, kind):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    if kind == "relative":
        candidate = Path("relative.json")
    elif kind == "dotdot":
        child = tmp_path / "child"
        child.mkdir()
        candidate = child / ".." / path.name
    elif kind == "missing_parent":
        candidate = tmp_path / "absent" / path.name
    else:
        candidate = tmp_path
    with pytest.raises(archive.DisconnectedFailureArchiveRejected):
        _review(plan, schedule, failures, candidate, witness.file_sha256)


@pytest.mark.parametrize("kind", ("symlink", "hardlink"))
def test_aliases_cannot_be_read_as_archive(tmp_path, kind):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    alias = tmp_path / "alias.json"
    try:
        if kind == "symlink":
            alias.symlink_to(path)
        else:
            alias.hardlink_to(path)
    except (OSError, NotImplementedError):
        pytest.skip("link creation unavailable on this filesystem")
    with pytest.raises(archive.DisconnectedFailureArchiveRejected):
        _review(plan, schedule, failures, alias, witness.file_sha256)


def test_concurrent_exclusive_creators_have_at_most_one_winner(tmp_path):
    plan, schedule, failures, receipt = _fixture()
    path = tmp_path / "contended.json"
    barrier = Barrier(2)

    def try_create():
        barrier.wait(timeout=10)
        try:
            return archive.archive_disconnected_failure_fixture(
                receipt, plan, schedule,
                retained_plan_digest=plan.plan_digest, path=path,
            )
        except archive.DisconnectedFailureArchiveRejected:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (pool.submit(try_create), pool.submit(try_create))
        results = [task.result(timeout=25) for task in futures]
    assert sum(item is not None for item in results) == 1
    winner = next(item for item in results if item is not None)
    assert _review(plan, schedule, failures, path, winner.file_sha256) == winner


def test_ambiguous_fsync_failure_never_automatically_retries(tmp_path, monkeypatch):
    plan, schedule, _, receipt = _fixture()
    path = tmp_path / "ambiguous.json"

    def fail_fsync(fd):
        raise OSError("synthetic fsync error")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="create-only"):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )
    assert path.exists()
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="create-only"):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )


def test_false_denial_getter_cannot_rewrite_final_witness(tmp_path, monkeypatch):
    plan, schedule, _, receipt = _fixture()

    def malicious_false(self):
        object.__setattr__(self, "terminal_counts", (0, 0, 0))
        return False

    monkeypatch.setattr(
        archive.ArchivedDisconnectedFailure,
        "real_outcome_proven",
        property(malicious_false),
    )
    path = tmp_path / "denial-quarantine.json"
    with pytest.raises(archive.DisconnectedFailureArchiveRejected, match="changed"):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )
    # The original denial definition is now checked before create-only I/O.
    assert not path.exists()


def test_file_changed_during_second_read_cannot_pass(tmp_path, monkeypatch):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    original = archive._read_once
    calls = 0

    def reentrant_read(candidate):
        nonlocal calls
        observed = original(candidate)
        calls += 1
        if calls == 1:
            raw = candidate.read_bytes()
            candidate.write_bytes(b"X" + raw[1:])
        return observed

    monkeypatch.setattr(archive, "_read_once", reentrant_read)
    with pytest.raises(archive.DisconnectedFailureArchiveRejected):
        _review(plan, schedule, failures, path, witness.file_sha256)
