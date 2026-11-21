"""A cached startup diagnosis cannot be altered by caller-ID callbacks.

Readiness is a disconnected fixture; it never authorizes a live backend.
"""

import pytest

import ark.startup_readiness_review as startup
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _snapshot():
    return evaluate_startup_readiness((
        StartupComponent("root", local_state=ReadinessState.BLOCKED),
        StartupComponent("child", dependencies=("root",)),
    ))


def test_clean_snapshot_still_preserves_dependency_blockers():
    snapshot = _snapshot()
    assert snapshot.state("root") is ReadinessState.BLOCKED
    assert snapshot.state("child") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("child") == ("root",)


@pytest.mark.parametrize("method", ("state", "root_blockers"))
def test_identifier_callback_cannot_reclassify_cached_blocker(
    monkeypatch, method,
):
    snapshot = _snapshot()
    original_integrity = StartupSnapshot._assert_integrity
    original_identifier = startup._identifier
    phase = {"passed": False, "attacked": False}

    def check(self):
        original_integrity(self)
        phase["passed"] = True

    def identify(value, label):
        result = original_identifier(value, label)
        if phase["passed"] and not phase["attacked"]:
            phase["attacked"] = True
            root = next(
                item for item in snapshot.components if item.component_id == "root"
            )
            if method == "state":
                child = next(
                    item for item in snapshot.components
                    if item.component_id == "child"
                )
                object.__setattr__(
                    child, "effective_state", ReadinessState.READY,
                )
            else:
                object.__setattr__(
                    root, "local_state", ReadinessState.READY,
                )
        return result

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", check)
    monkeypatch.setattr(startup, "_identifier", identify)
    with pytest.raises(ValueError, match="startup snapshot"):
        if method == "state":
            snapshot.state("child")
        else:
            snapshot.root_blockers("child")
    assert phase["attacked"]
