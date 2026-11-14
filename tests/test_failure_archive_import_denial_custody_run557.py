"""Detached FAILED/BLOCKED archives reject substituted denial definitions.

These are local, hypothetical fixture artifacts; they never certify a real
failure, invoke ToolBackend, or authorize retry and replay.
"""

from __future__ import annotations

import pytest
from test_disconnected_failure_archive_run534 import _fixture, _review, _write

from ark.agency import disconnected_batch_failure_archive as archive

_FLAGS = (
    "external_dispatch_authorized",
    "write_authorized",
    "automatic_replay_authorized",
    "failure_authenticated",
    "real_outcome_proven",
)


@pytest.mark.parametrize("flag", _FLAGS)
def test_preinstalled_false_only_denial_prevents_create(tmp_path, monkeypatch, flag):
    plan, schedule, _, receipt = _fixture()
    path = tmp_path / "never-created.json"
    monkeypatch.setattr(
        archive.ArchivedDisconnectedFailure, flag, property(lambda _self: False),
    )
    with pytest.raises(
        archive.DisconnectedFailureArchiveRejected, match="definition changed",
    ):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )
    assert not path.exists()


@pytest.mark.parametrize("flag", _FLAGS)
def test_preinstalled_false_only_denial_prevents_restart_review(
    tmp_path, monkeypatch, flag,
):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    monkeypatch.setattr(
        archive.ArchivedDisconnectedFailure, flag, property(lambda _self: False),
    )
    with pytest.raises(
        archive.DisconnectedFailureArchiveRejected, match="definition changed",
    ):
        _review(plan, schedule, failures, path, witness.file_sha256)


def test_denial_replaced_during_verification_prevents_creation(tmp_path, monkeypatch):
    plan, schedule, _, receipt = _fixture()
    path = tmp_path / "not-created-after-verifier.json"
    original = archive.verify_disconnected_failure_fixture

    def replace_after_verify(*args, **kwargs):
        output = original(*args, **kwargs)
        monkeypatch.setattr(
            archive.ArchivedDisconnectedFailure,
            "write_authorized",
            property(lambda _self: False),
        )
        return output

    monkeypatch.setattr(
        archive, "verify_disconnected_failure_fixture", replace_after_verify,
    )
    with pytest.raises(
        archive.DisconnectedFailureArchiveRejected, match="definition changed",
    ):
        archive.archive_disconnected_failure_fixture(
            receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
            path=path,
        )
    assert not path.exists()


def test_denial_replaced_during_archive_read_prevents_restart(tmp_path, monkeypatch):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    original = archive._read_once
    calls = []

    def replace_on_read(candidate):
        result = original(candidate)
        calls.append(1)
        if len(calls) == 1:
            monkeypatch.setattr(
                archive.ArchivedDisconnectedFailure,
                "automatic_replay_authorized",
                property(lambda _self: False),
            )
        return result

    monkeypatch.setattr(archive, "_read_once", replace_on_read)
    with pytest.raises(
        archive.DisconnectedFailureArchiveRejected, match="definition changed",
    ):
        _review(plan, schedule, failures, path, witness.file_sha256)
    assert calls


def test_original_denials_allow_hypothetical_failure_roundtrip(tmp_path):
    plan, schedule, failures, _, path, witness = _write(tmp_path)
    result = _review(plan, schedule, failures, path, witness.file_sha256)
    assert result.terminal_counts == (1, 1, 1)
    for flag in _FLAGS:
        assert getattr(result, flag) is False
