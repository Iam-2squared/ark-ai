"""Durable fixture-only batch cycle archive; no actual action or replay."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

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

REQ = "req_" + "a" * 32


def _fixture():
    first = DisconnectedBatchStep(
        "step_" + "1" * 16, "math.sum", '{"values":[1,2]}',
    )
    second = DisconnectedBatchStep(
        "step_" + "2" * 16, "text.stats",
        '{"text":"private synthetic phrase"}',
    )
    third = DisconnectedBatchStep(
        "step_" + "3" * 16, "text.find",
        '{"needle":"x","text":"xyz"}',
        (first.step_id, second.step_id),
    )
    plan = build_disconnected_batch_plan(REQ, (first, second, third))
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    receipt = simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=plan.plan_digest,
    )
    return plan, schedule, receipt


def _write(tmp_path):
    plan, schedule, receipt = _fixture()
    path = tmp_path / "synthetic-cycle.json"
    witness = archive.archive_disconnected_batch_fixture_cycle(
        receipt, plan, schedule,
        retained_plan_digest=plan.plan_digest, path=path,
    )
    return plan, schedule, receipt, path, witness


def _review(plan, schedule, path, sha):
    return archive.review_disconnected_batch_fixture_cycle_archive(
        plan, schedule, retained_plan_digest=plan.plan_digest,
        path=path, retained_file_sha256=sha,
    )


def test_create_only_roundtrip_and_restarted_fixture_read(tmp_path):
    plan, schedule, receipt, path, saved = _write(tmp_path)
    assert path.is_file()
    assert path.read_bytes()
    assert b"private synthetic phrase" not in path.read_bytes()
    restarted_plan, restarted_schedule, restarted_receipt = _fixture()
    assert restarted_plan is not plan
    assert restarted_receipt is not receipt
    result = _review(restarted_plan, restarted_schedule, path, saved.file_sha256)
    assert result == saved
    assert result.request_id == REQ
    assert result.plan_digest == plan.plan_digest
    assert result.cycle_digest == receipt.cycle_digest
    assert saved.external_dispatch_authorized is False
    assert saved.write_authorized is False
    assert saved.automatic_replay_authorized is False
    assert saved.real_outcome_proven is False


def test_preexisting_file_is_never_overwritten(tmp_path):
    plan, schedule, receipt = _fixture()
    path = tmp_path / "synthetic-cycle.json"
    path.write_bytes(b"preexisting user bytes")
    with pytest.raises(archive.DisconnectedBatchArchiveRejected, match="create-only"):
        archive.archive_disconnected_batch_fixture_cycle(
            receipt, plan, schedule,
            retained_plan_digest=plan.plan_digest, path=path,
        )
    assert path.read_bytes() == b"preexisting user bytes"


@pytest.mark.parametrize("kind", ("mutated", "different_sha", "empty", "extra_key"))
def test_recovery_refuses_altered_file_or_independent_digest(tmp_path, kind):
    plan, schedule, _, path, saved = _write(tmp_path)
    pin = saved.file_sha256
    if kind == "mutated":
        raw = path.read_bytes()
        path.write_bytes(b"X" + raw[1:])
    elif kind == "different_sha":
        pin = "0" * 64 if pin != "0" * 64 else "f" * 64
    elif kind == "empty":
        path.write_bytes(b"")
    else:
        raw = path.read_bytes()
        path.write_bytes(raw[:-1] + b',"unexpected":true}')
    with pytest.raises(archive.DisconnectedBatchArchiveRejected):
        _review(plan, schedule, path, pin)


def test_stale_plan_digest_rejected_before_creating_archive(tmp_path):
    plan, schedule, receipt = _fixture()
    path = tmp_path / "uncreated.json"
    with pytest.raises(ValueError):
        archive.archive_disconnected_batch_fixture_cycle(
            receipt, plan, schedule,
            retained_plan_digest="f" * 64, path=path,
        )
    assert not path.exists()


@pytest.mark.parametrize("kind", ("relative", "dotdot", "missing_parent", "directory"))
def test_path_aliases_and_nonfiles_rejected(tmp_path, kind):
    plan, schedule, _, path, saved = _write(tmp_path)
    if kind == "relative":
        candidate = Path("synthetic-cycle.json")
    elif kind == "dotdot":
        child = tmp_path / "child"
        child.mkdir()
        candidate = child / ".." / path.name
    elif kind == "missing_parent":
        candidate = tmp_path / "absent" / path.name
    else:
        candidate = tmp_path
    with pytest.raises(archive.DisconnectedBatchArchiveRejected):
        _review(plan, schedule, candidate, saved.file_sha256)


@pytest.mark.parametrize("kind", ("symlink", "hardlink"))
def test_file_aliases_are_not_valid_archives(tmp_path, kind):
    plan, schedule, _, path, saved = _write(tmp_path)
    candidate = tmp_path / "alias.json"
    try:
        if kind == "symlink":
            candidate.symlink_to(path)
        else:
            candidate.hardlink_to(path)
    except (OSError, NotImplementedError):
        pytest.skip("filesystem link creation unavailable")
    with pytest.raises(archive.DisconnectedBatchArchiveRejected):
        _review(plan, schedule, candidate, saved.file_sha256)


def test_file_swap_during_independent_second_read_rejected(tmp_path, monkeypatch):
    plan, schedule, _, path, saved = _write(tmp_path)
    original = archive._read_once
    calls = 0

    def read_and_mutate(source):
        nonlocal calls
        result = original(source)
        calls += 1
        if calls == 1:
            data = source.read_bytes()
            source.write_bytes(b"X" + data[1:])
        return result

    monkeypatch.setattr(archive, "_read_once", read_and_mutate)
    with pytest.raises(archive.DisconnectedBatchArchiveRejected):
        _review(plan, schedule, path, saved.file_sha256)


def test_failed_fsync_leaves_quarantined_file_without_retry(tmp_path, monkeypatch):
    plan, schedule, receipt = _fixture()
    path = tmp_path / "ambiguous.json"

    def denied_sync(fd):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(os, "fsync", denied_sync)
    with pytest.raises(archive.DisconnectedBatchArchiveRejected, match="create-only"):
        archive.archive_disconnected_batch_fixture_cycle(
            receipt, plan, schedule,
            retained_plan_digest=plan.plan_digest, path=path,
        )
    assert path.exists()
    with pytest.raises(archive.DisconnectedBatchArchiveRejected, match="create-only"):
        archive.archive_disconnected_batch_fixture_cycle(
            receipt, plan, schedule,
            retained_plan_digest=plan.plan_digest, path=path,
        )


def test_concurrent_create_only_writers_have_single_winner(tmp_path):
    plan, schedule, receipt = _fixture()
    path = tmp_path / "same-cycle.json"
    barrier = Barrier(2)

    def write():
        barrier.wait(timeout=10)
        try:
            return archive.archive_disconnected_batch_fixture_cycle(
                receipt, plan, schedule,
                retained_plan_digest=plan.plan_digest, path=path,
            )
        except archive.DisconnectedBatchArchiveRejected:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (pool.submit(write), pool.submit(write))
        results = [future.result(timeout=20) for future in futures]
    assert sum(result is not None for result in results) == 1
    winner = next(result for result in results if result is not None)
    assert _review(plan, schedule, path, winner.file_sha256) == winner


def test_class_authority_override_denied_without_writing(tmp_path, monkeypatch):
    plan, schedule, receipt = _fixture()
    monkeypatch.setattr(
        archive.ArchivedDisconnectedBatchCycle,
        "write_authorized", property(lambda self: True),
    )
    path = tmp_path / "should-not-be-authorized.json"
    with pytest.raises(archive.DisconnectedBatchArchiveRejected, match="authority"):
        archive.archive_disconnected_batch_fixture_cycle(
            receipt, plan, schedule,
            retained_plan_digest=plan.plan_digest, path=path,
        )
    # The archive can already be durably created when a final witness check
    # rejects. There must never be a destructive automatic rollback.
    assert path.exists()
