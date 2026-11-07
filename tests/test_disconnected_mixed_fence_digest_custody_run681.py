"""A detached mixed-plan recovery fence uses only its original digest code.

No tool execution, SQLite, real permission or authenticated approval is used.
Identical-value domain substitution still represents a different code epoch.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_write_recovery_fence as recovery

_PLAN = "plan_" + "9" * 64
_ROOT = "step_" + "1" * 16
_CHILD = "step_" + "2" * 16


def _claims():
    return (
        recovery.OfflineRecoveryStepClaim(_ROOT, "WRITE", (), "UNKNOWN"),
        recovery.OfflineRecoveryStepClaim(
            _CHILD, "READ", (_ROOT,), "PENDING",
        ),
    )


@pytest.mark.parametrize(
    "tamper",
    ("hashlib", "json", "sha256", "dumps", "domain", "equal_domain"),
)
def test_changed_digest_definition_rejected_before_any_injected_callback(
    monkeypatch, tamper,
):
    claims = _claims()
    original = recovery.review_disconnected_recovery_fence(_PLAN, claims)
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append(tamper)
        raise AssertionError("substituted digest code must never execute")

    with monkeypatch.context() as patch:
        if tamper == "hashlib":
            patch.setattr(recovery, "hashlib", object())
        elif tamper == "json":
            patch.setattr(recovery, "json", object())
        elif tamper == "sha256":
            patch.setattr(recovery.hashlib, "sha256", forbidden)
        elif tamper == "dumps":
            patch.setattr(recovery.json, "dumps", forbidden)
        elif tamper == "domain":
            patch.setattr(recovery, "_DOMAIN", b"unreviewed-domain")
        else:
            equivalent = bytes(bytearray(recovery._DOMAIN))
            assert equivalent == recovery._DOMAIN
            assert equivalent is not recovery._DOMAIN
            patch.setattr(recovery, "_DOMAIN", equivalent)
        with pytest.raises(
            recovery.OfflineRecoveryFenceRejected,
            match="mixed-plan digest implementation or domain changed",
        ):
            recovery.review_disconnected_recovery_fence(_PLAN, claims)

    assert calls == []
    restored = recovery.review_disconnected_recovery_fence(_PLAN, claims)
    assert restored == original
    assert tuple(item.code for item in restored.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert restored.dispatch_authorized is False
    assert restored.automatic_replay_authorized is False
    assert restored.write_authorized is False
    assert restored.external_outcome_verified is False
