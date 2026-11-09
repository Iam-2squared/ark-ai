"""Local READ recovery cannot change its accepted graph or digest contract.

All steps are synthetic. READY_MOCK_ONLY is never a live tool authorization;
hashes and input state cannot prove actual execution or independent custody.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_read_recovery_schedule as recovery

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16

_MUTATIONS = (
    ("_DOMAIN", b"unreviewed-recovery-domain\\0"),
    ("_REQUEST", re.compile(r"req_.*\\Z")),
    ("_STEP", re.compile(r"step_.*\\Z")),
    ("_SHA", re.compile(r".*\\Z")),
    ("_OPS", frozenset(("shell.exec", "math.sum"))),
    ("_STATES", frozenset(("SUCCEEDED", "NOT_STARTED", "UNREVIEWED"))),
)


@pytest.mark.parametrize(("name", "replacement"), _MUTATIONS)
def test_rebound_recovery_contract_denied_before_accessing_steps(
    monkeypatch, name, replacement,
):
    monkeypatch.setattr(recovery, name, replacement)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="recovery schedule authority descriptor changed",
    ):
        recovery.schedule_detached_read_recovery(REQUEST, None)


def test_equal_value_domain_rebinding_is_a_different_review_epoch(monkeypatch):
    alternate = bytes(bytearray(recovery._DOMAIN))
    assert alternate == recovery._DOMAIN and alternate is not recovery._DOMAIN
    monkeypatch.setattr(recovery, "_DOMAIN", alternate)
    with pytest.raises(recovery.DetachedReadRecoveryRejected):
        recovery.schedule_detached_read_recovery(REQUEST, None)


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
def test_injected_hash_and_json_callbacks_never_see_read_plan(
    monkeypatch, dependency,
):
    calls = []

    def poisoned(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("untrusted callback was executed")

    if dependency == "sha256":
        monkeypatch.setattr(recovery.hashlib, "sha256", poisoned)
    else:
        monkeypatch.setattr(recovery.json, "dumps", poisoned)
    with pytest.raises(
        recovery.DetachedReadRecoveryRejected,
        match="recovery schedule authority descriptor changed",
    ):
        recovery.schedule_detached_read_recovery(
            REQUEST,
            (recovery.ReadRecoveryStep(STEP, "math.sum", (), "NOT_STARTED"),),
        )
    assert calls == []


def test_original_recovery_contract_only_offers_disconnected_hint():
    review = recovery.schedule_detached_read_recovery(
        REQUEST,
        (recovery.ReadRecoveryStep(STEP, "math.sum", (), "NOT_STARTED"),),
    )
    assert tuple(step.disposition for step in review.decisions) == ("READY_MOCK_ONLY",)
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.external_outcome_verified is False
