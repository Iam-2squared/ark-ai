"""Cached startup readiness is still local-only after a traversal callback.

A READY report never authorizes real tools, notifications, credentials or
background actions. Integrity is checked after the final graph field lookup.
"""

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def snapshot():
    return evaluate_startup_readiness((
        StartupComponent("root", local_state=ReadinessState.BLOCKED),
        StartupComponent("child", dependencies=("root",)),
    ))


def test_unmodified_state_and_blocker_queries_remain_stable():
    stored = snapshot()
    assert stored.state("root") is ReadinessState.BLOCKED
    assert stored.state("child") is ReadinessState.DEPENDENCY_BLOCKED
    assert stored.root_blockers("child") == ("root",)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("local_state", ReadinessState.READY),
        ("effective_state", ReadinessState.READY),
        ("failure_code", "reflected-change"),
        ("schema_revision", "reflected-change"),
    ),
)
def test_state_lookup_rejects_reentrant_snapshot_edit(
    monkeypatch, field, replacement,
):
    stored = snapshot()
    original = StartupSnapshot._assert_integrity
    checks = 0

    def modified(self):
        nonlocal checks
        checks += 1
        original(self)
        if checks == 2:
            root = next(
                item for item in self.components if item.component_id == "root"
            )
            object.__setattr__(root, field, replacement)

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", modified)
    with pytest.raises(ValueError, match="startup snapshot"):
        stored.state("child")
    assert checks >= 3


@pytest.mark.parametrize("target", ("root_state", "dependency", "digest"))
def test_blocker_traversal_rejects_reentrant_snapshot_edit(monkeypatch, target):
    stored = snapshot()
    original = StartupSnapshot._assert_integrity
    checks = 0

    def modified(self):
        nonlocal checks
        checks += 1
        original(self)
        if checks == 2:
            root = next(
                item for item in self.components if item.component_id == "root"
            )
            child = next(
                item for item in self.components if item.component_id == "child"
            )
            if target == "root_state":
                object.__setattr__(root, "local_state", ReadinessState.READY)
            elif target == "dependency":
                object.__setattr__(child, "dependencies", ())
            else:
                object.__setattr__(self, "digest", "startup_" + "f" * 64)

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", modified)
    with pytest.raises(ValueError, match="startup snapshot"):
        stored.root_blockers("child")
    assert checks >= 3
