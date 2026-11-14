"""Disconnected schedule restart review refuses substituted digest or grammar.

This uses no timer, notification, trusted clock, real sensor, or ToolBackend.
A locally coherent quarantine witness never establishes caller consent.
"""

from __future__ import annotations

import pytest

from ark import offline_schedule_resume_review as resume
from ark.disconnected_schedule_preview import (
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
)
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    genesis_quarantine_witness,
)


def _fixture(tmp_path):
    policy = DisconnectedSchedulePolicy("a" * 64, 1000, 1000, 3, 100)
    qpolicy = QuarantinePolicy("a" * 64, 1000, 1000, 3, 100)
    ledger = DisconnectedScheduleQuarantineLedger(
        tmp_path / "quarantine.sqlite", policy=qpolicy, create=True,
    )
    return ledger, policy, DisconnectedScheduleCursor(0), genesis_quarantine_witness(
        qpolicy,
    )


def _review(ledger, policy, cursor, witness):
    return resume.review_offline_schedule_resume(
        ledger, policy, cursor, retained_quarantine=witness, observed_now_ms=1000,
    )


@pytest.mark.parametrize(
    "dependency", ("sha256", "json.dumps", "grammar", "domain"),
)
def test_preinstalled_codec_change_rejected_before_quarantine_read(
    tmp_path, monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    ledger, policy, cursor, witness = _fixture(tmp_path)
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(dependency)
        raise AssertionError("substituted callback or ledger read executed")

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "inspect", forbidden)
        if dependency == "sha256":
            patch.setattr(resume.hashlib, "sha256", forbidden)
        elif dependency == "json.dumps":
            patch.setattr(resume.json, "dumps", forbidden)
        elif dependency == "grammar":
            patch.setattr(resume, "_SHA", object())
        else:
            patch.setattr(resume, "_DOMAIN", b"unreviewed-domain")
        with pytest.raises(
            resume.ScheduleResumeRejected,
            match="offline resume digest or grammar authority changed",
        ):
            _review(ledger, policy, cursor, witness)
    assert invoked == []


def test_preview_callback_cannot_replace_json_codec_for_resume_review(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger, policy, cursor, witness = _fixture(tmp_path)
    native = resume.preview_disconnected_schedule
    invoked: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append("json.dumps")
        raise AssertionError("substituted serializer executed")

    with monkeypatch.context() as patch:
        def preview_then_swap(*args, **kwargs):
            value = native(*args, **kwargs)
            patch.setattr(resume.json, "dumps", forbidden)
            return value

        patch.setattr(resume, "preview_disconnected_schedule", preview_then_swap)
        with pytest.raises(
            resume.ScheduleResumeRejected,
            match="offline resume digest or grammar authority changed",
        ):
            _review(ledger, policy, cursor, witness)
    assert invoked == []


def test_unmodified_resume_remains_read_only_and_denied(tmp_path) -> None:
    ledger, policy, cursor, witness = _fixture(tmp_path)
    first = _review(ledger, policy, cursor, witness)
    second = _review(ledger, policy, cursor, witness)
    assert first == second
    assert first.next_state == "DUE_UNVERIFIED"
    assert first.notification_authorized is False
    assert first.tool_execution_authorized is False
    assert first.trusted_clock_verified is False
    assert ledger.inspect(retained=witness) == witness
