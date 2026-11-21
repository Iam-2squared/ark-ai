"""Disconnected startup readiness must never execute a forged constructor.

Only synthetic probes are evaluated; READY does not enable actual backends.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.startup_readiness_review as startup


def _probes():
    return (
        startup.StartupComponent("memory", local_state=startup.ReadinessState.BLOCKED),
        startup.StartupComponent("agent", ("memory",)),
    )


@pytest.mark.parametrize(
    ("klass", "hook"),
    (
        ("StartupComponent", "__init__"),
        ("StartupComponent", "__post_init__"),
        ("ComponentResult", "__init__"),
        ("StartupSnapshot", "__init__"),
    ),
)
def test_preinstalled_counterfeit_startup_constructor_never_runs(
    monkeypatch, klass, hook,
):
    probes = _probes()
    invoked = []

    def hostile(*args):
        invoked.append(args)
        raise AssertionError("startup constructor should not execute")

    monkeypatch.setattr(getattr(startup, klass), hook, hostile)
    with pytest.raises(ValueError, match="startup constructor authority changed"):
        startup.evaluate_startup_readiness(probes)
    assert invoked == []


@pytest.mark.parametrize(
    "klass",
    ("StartupComponent", "ComponentResult", "StartupSnapshot"),
)
def test_probe_iterator_cannot_replace_a_later_startup_constructor(
    monkeypatch, klass,
):
    probes = _probes()
    invoked = []

    def hostile(*args):
        invoked.append(args)
        raise AssertionError("startup constructor should not execute")

    def stream():
        yield probes[0]
        monkeypatch.setattr(getattr(startup, klass), "__init__", hostile)
        yield probes[1]

    with pytest.raises(ValueError, match="startup constructor authority changed"):
        startup.evaluate_startup_readiness(stream())
    assert invoked == []


def test_digest_callback_cannot_swap_final_snapshot_constructor(monkeypatch):
    probes = _probes()
    invoked = []
    original_hash = startup.hashlib.sha256

    def hostile(*args):
        invoked.append(args)
        raise AssertionError("startup snapshot constructor should not execute")

    def hash_and_swap(encoded):
        result = original_hash(encoded)
        monkeypatch.setattr(startup.StartupSnapshot, "__init__", hostile)
        return result

    monkeypatch.setattr(
        startup, "hashlib", SimpleNamespace(sha256=hash_and_swap),
    )
    with pytest.raises(ValueError, match="startup constructor authority changed"):
        startup.evaluate_startup_readiness(probes)
    assert invoked == []


def test_unmodified_startup_remains_inert_and_dependency_blocked():
    snapshot = startup.evaluate_startup_readiness(_probes())
    assert snapshot.state("memory") is startup.ReadinessState.BLOCKED
    assert snapshot.state("agent") is startup.ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("agent") == ("memory",)
