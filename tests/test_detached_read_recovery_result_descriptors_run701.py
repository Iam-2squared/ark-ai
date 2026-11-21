"""Detached Planner recovery output descriptors are never execution authority.

Tests use only synthetic graph records. No ToolBackend, model or live dispatch.
A hostile inherited __new__ mutation is isolated because CPython class
allocation slots are not reliably restored by setattr/delattr in one process.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

import ark.agency.disconnected_read_recovery_schedule as mod

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _review():
    return mod.schedule_detached_read_recovery(
        _REQUEST,
        (mod.ReadRecoveryStep(_STEP, "math.sum", (), "NOT_STARTED"),),
    )


@pytest.mark.parametrize(("carrier", "field"), (
    ("decision", "step_id"), ("decision", "disposition"),
    ("schedule", "request_id"), ("schedule", "decisions"),
    ("schedule", "schedule_digest"),
    ("decision", "__getattribute__"), ("decision", "__getattr__"),
    ("schedule", "__getattribute__"), ("schedule", "__getattr__"),
))
def test_preinstalled_hostile_result_descriptor_refused_before_callback(
    monkeypatch, carrier, field,
):
    cls = (
        mod.ReadRecoveryDecision
        if carrier == "decision" else mod.DetachedReadRecoverySchedule
    )
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("malicious descriptor")
        raise AssertionError("hostile result descriptor executed")

    replacement = property(forbidden) if not field.startswith("__") else forbidden
    monkeypatch.setattr(cls, field, replacement, raising=False)
    with pytest.raises(
        mod.DetachedReadRecoveryRejected, match="authority descriptor changed",
    ):
        _review()
    assert calls == []


@pytest.mark.parametrize("carrier", ("decision", "schedule"))
def test_inherited_new_mutation_detected_in_isolated_interpreter(carrier):
    script = """
import sys
import ark.agency.disconnected_read_recovery_schedule as mod
cls = (mod.ReadRecoveryDecision if sys.argv[1] == 'decision'
       else mod.DetachedReadRecoverySchedule)
calls = []
def forbidden(*_a, **_kw):
    calls.append(True)
    raise AssertionError('forged constructor executed')
cls.__new__ = forbidden
try:
    mod._assert_original_denials()
except mod.DetachedReadRecoveryRejected as exc:
    assert 'authority descriptor changed' in str(exc)
else:
    raise AssertionError('forged __new__ accepted')
assert not calls
"""
    result = subprocess.run(
        [sys.executable, "-c", script, carrier],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(("carrier", "field"), (
    ("decision", "disposition"), ("schedule", "decisions"),
))
def test_substituted_digest_cannot_install_hostile_result_slot(
    monkeypatch, carrier, field,
):
    cls = (
        mod.ReadRecoveryDecision
        if carrier == "decision" else mod.DetachedReadRecoverySchedule
    )
    original_hash = mod.hashlib.sha256
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("forged result read")
        raise AssertionError("unreviewed slot executed")

    def reentrant_hash(payload=b""):
        if payload.startswith(mod._DOMAIN):
            calls.append("digest")
            monkeypatch.setattr(cls, field, property(forbidden))
        return original_hash(payload)

    monkeypatch.setattr(mod.hashlib, "sha256", reentrant_hash)
    with pytest.raises(
        mod.DetachedReadRecoveryRejected, match="authority descriptor changed",
    ):
        _review()
    # Reject a replaced SHA callback before it can inject any output slot.
    assert calls == []


def test_unmodified_graph_yields_non_authorizing_mock_hint():
    plan = _review()
    assert [step.disposition for step in plan.decisions] == ["READY_MOCK_ONLY"]
    assert plan.dispatch_authorized is False
    assert plan.automatic_replay_authorized is False
    assert plan.external_outcome_verified is False
