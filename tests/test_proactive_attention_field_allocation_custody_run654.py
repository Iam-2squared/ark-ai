"""Disconnected attention inputs reject replaced slots before reading metadata.

Only synthetic hash identifiers, never notifications, tools, sensors, consent,
or a trusted-clock signal. Inherited __new__ tests use child interpreters.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark import proactive_attention_preview as attention

_POLICY_FIELDS = (
    "scope_sha256", "trigger_sha256", "cooldown_ms", "rolling_window_ms",
    "max_surfaced_per_window", "suppress_unchanged",
)
_MARKER_FIELDS = (
    "scope_sha256", "trigger_sha256", "occurrence_sha256",
    "observation_sha256", "surfaced_at_ms",
)


def _inputs():
    policy = attention.AttentionBudgetPolicy(
        "a" * 64, "b" * 64, 1, 100, 2, False,
    )
    row = attention.SyntheticSurfaceMarker(
        "a" * 64, "b" * 64, "c" * 64, "d" * 64, 90,
    )
    return policy, (row,)


def _preview(policy, rows):
    return attention.preview_proactive_attention(
        policy, rows, occurrence_sha256="e" * 64,
        observation_sha256="f" * 64, observed_now_ms=100,
    )


def _install(monkeypatch, kind, name, hits):
    def poisoned(*_args, **_kwargs):
        hits.append(name)
        raise AssertionError("poisoned policy/history hook executed")

    replacement = property(poisoned) if name in (
        _POLICY_FIELDS + _MARKER_FIELDS
    ) else poisoned
    monkeypatch.setattr(kind, name, replacement, raising=False)


@pytest.mark.parametrize("target,name", (
    *(("policy", field) for field in _POLICY_FIELDS),
    *(("marker", field) for field in _MARKER_FIELDS),
    ("policy", "__init__"),
    ("marker", "__init__"),
))
def test_preinstalled_policy_or_marker_slot_does_not_execute(
    monkeypatch, target, name,
):
    policy, rows = _inputs()
    hits = []
    carrier = (
        attention.AttentionBudgetPolicy if target == "policy"
        else attention.SyntheticSurfaceMarker
    )
    _install(monkeypatch, carrier, name, hits)
    with pytest.raises(
        attention.AttentionPreviewRejected,
        match="attention authority definition changed",
    ):
        _preview(policy, rows)
    assert hits == []


@pytest.mark.parametrize("target,name", (
    ("policy", "scope_sha256"),
    ("policy", "suppress_unchanged"),
    ("marker", "occurrence_sha256"),
    ("marker", "surfaced_at_ms"),
    ("policy", "__init__"),
    ("marker", "__init__"),
))
def test_substituted_digest_cannot_reinstall_input_field_or_constructor(
    monkeypatch, target, name,
):
    policy, rows = _inputs()
    carrier = (
        attention.AttentionBudgetPolicy if target == "policy"
        else attention.SyntheticSurfaceMarker
    )
    original_sha = attention.hashlib.sha256
    hits = []
    count = []

    def corrupt_on_digest(payload=b""):
        if payload.startswith(attention._DOMAIN) and not count:
            count.append(1)
            _install(monkeypatch, carrier, name, hits)
        return original_sha(payload)

    monkeypatch.setattr(attention.hashlib, "sha256", corrupt_on_digest)
    with pytest.raises(
        attention.AttentionPreviewRejected,
        match="attention authority definition changed",
    ):
        _preview(policy, rows)
    assert count == []
    assert hits == []


@pytest.mark.parametrize("target", ("policy", "marker"))
def test_inherited_new_injected_only_in_separate_process(target):
    # CPython's tp_new slot may remain poisoned even if __new__ is removed.
    script = textwrap.dedent("""
        from ark import proactive_attention_preview as attention

        policy = attention.AttentionBudgetPolicy(
            "a" * 64, "b" * 64, 1, 100, 2, False,
        )
        row = attention.SyntheticSurfaceMarker(
            "a" * 64, "b" * 64, "c" * 64, "d" * 64, 90,
        )
        hits = []

        def poisoned(*args, **kwargs):
            hits.append("new")
            raise AssertionError("allocation hook reached")

        kind = (
            attention.AttentionBudgetPolicy
            if TARGET == "policy" else attention.SyntheticSurfaceMarker
        )
        kind.__new__ = staticmethod(poisoned)
        try:
            attention.preview_proactive_attention(
                policy, (row,), occurrence_sha256="e" * 64,
                observation_sha256="f" * 64, observed_now_ms=100,
            )
        except attention.AttentionPreviewRejected as exc:
            assert "attention authority definition changed" in str(exc)
        else:
            raise AssertionError("poisoned allocation hook accepted")
        assert hits == []
    """).replace("TARGET", repr(target))
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True,
        text=True, check=False, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_healthy_policy_history_remains_local_denial_only():
    policy, rows = _inputs()
    result = _preview(policy, rows)
    # The 90ms row is outside the 1ms cooldown at a 100ms review.
    assert result.disposition == "REVIEW_ONLY"
    assert result.notification_authorized is False
    assert result.action_authorized is False
    assert result.consent_verified is False
    assert result.trusted_clock_verified is False
