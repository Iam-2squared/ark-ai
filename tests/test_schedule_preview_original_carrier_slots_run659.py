"""Scheduler policy/cursor/result reflectively patched slots must fail closed.

All recurrence times are caller-asserted fixture values. This module never
runs timers, grants notification permissions, or dispatches a tool backend.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.disconnected_schedule_preview as mod


def _inputs():
    return (
        mod.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500),
        mod.DisconnectedScheduleCursor(0),
    )


@pytest.mark.parametrize(
    "kind,name",
    (
        ("policy", "policy_sha256"),
        ("policy", "first_due_at_ms"),
        ("policy", "interval_ms"),
        ("policy", "__getattribute__"),
        ("cursor", "next_index"),
        ("cursor", "last_occurrence_id"),
        ("cursor", "__getattr__"),
        ("result", "state"),
        ("result", "next_index"),
        ("result", "fingerprint"),
        ("result", "__init__"),
    ),
)
def test_preinstalled_executable_carrier_rejected_without_hashing(
    monkeypatch, kind, name,
):
    policy, cursor = _inputs()
    chosen = {
        "policy": mod.DisconnectedSchedulePolicy,
        "cursor": mod.DisconnectedScheduleCursor,
        "result": mod.DisconnectedDuePreview,
    }[kind]
    invoked = []

    def poison(*_args, **_kwargs):
        invoked.append(name)
        raise AssertionError("unreviewed scheduler carrier executed")

    replacement = property(poison) if not name.startswith("__") else poison

    def forbidden_hash(*_args, **_kwargs):
        raise AssertionError("scheduler hashed unreviewed input")

    with monkeypatch.context() as patch:
        patch.setattr(chosen, name, replacement, raising=False)
        patch.setattr(mod.hashlib, "sha256", forbidden_hash)
        with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
            mod.preview_disconnected_schedule(
                policy, cursor, observed_now_ms=10_000,
            )
    assert invoked == []


@pytest.mark.parametrize("target", ("result", "cursor"))
def test_hash_callback_cannot_install_new_field_getter(
    monkeypatch, target,
):
    policy, cursor = _inputs()
    calls = []
    cls, field = (
        (mod.DisconnectedDuePreview, "fingerprint")
        if target == "result" else
        (mod.DisconnectedScheduleCursor, "next_index")
    )
    original = mod.hashlib.sha256

    def forged(_self):
        calls.append("getter")
        raise AssertionError("new getter executed after hash")

    def injected(*args, **kwargs):
        # Install the substituted slot after computing an ordinary hash,
        # then retain it until the preview has been rejected.
        digest = original(*args, **kwargs)
        monkeypatch.setattr(cls, field, property(forged))
        return digest

    with monkeypatch.context() as patch:
        patch.setattr(mod.hashlib, "sha256", injected)
        with pytest.raises(mod.SchedulePreviewRejected, match="carrier changed"):
            mod.preview_disconnected_schedule(
                policy, cursor, observed_now_ms=10_000,
            )
    assert calls == []


@pytest.mark.parametrize("target", ("policy", "result"))
def test_inherited_allocation_poison_stays_in_separate_python_process(target):
    script = textwrap.dedent(f"""
        import ark.disconnected_schedule_preview as mod

        policy = mod.DisconnectedSchedulePolicy("a" * 64, 10000, 5000, 3, 500)
        cursor = mod.DisconnectedScheduleCursor(0)
        cls = (
            mod.DisconnectedSchedulePolicy
            if {target!r} == "policy" else mod.DisconnectedDuePreview
        )
        called = []

        def poison(*args, **kwargs):
            called.append("new")
            raise AssertionError("poisoned allocation ran")

        cls.__new__ = staticmethod(poison)
        try:
            mod.preview_disconnected_schedule(policy, cursor, observed_now_ms=10000)
        except mod.SchedulePreviewRejected as exc:
            assert "carrier changed" in str(exc)
        else:
            raise AssertionError("replaced allocation accepted")
        assert called == []
    """)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_original_scheduler_remains_non_authorizing():
    policy, cursor = _inputs()
    result = mod.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )
    assert result.state == "DUE_UNVERIFIED"
    for name in mod._DENIAL_NAMES:
        assert getattr(result, name) is False
