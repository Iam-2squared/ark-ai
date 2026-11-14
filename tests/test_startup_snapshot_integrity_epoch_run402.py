"""Readiness integrity validators cannot silently rebase original carriers.

Disconnected fixture evaluations only: a READY state is not a permission to
connect a backend or perform an actual external action.
"""

import pytest

import ark.startup_readiness_review as startup
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _snapshot():
    return evaluate_startup_readiness((
        StartupComponent("root", local_state=ReadinessState.BLOCKED),
        StartupComponent("child", dependencies=("root",)),
    ))


@pytest.mark.parametrize("mutation", ("local_state", "schema_revision", "tuple"))
def test_transient_component_drift_is_rejected_during_first_identifier(
    monkeypatch, mutation,
):
    snapshot = _snapshot()
    root = next(
        item for item in snapshot.components if item.component_id == "root"
    )
    components = snapshot.components
    original_id = startup._identifier
    seen = []

    def identifying(value, label):
        result = original_id(value, label)
        seen.append(label)
        if len(seen) == 1:
            if mutation == "local_state":
                object.__setattr__(root, "local_state", ReadinessState.READY)
            elif mutation == "schema_revision":
                object.__setattr__(root, "schema_revision", "temporary")
            else:
                object.__setattr__(
                    snapshot, "components", tuple(list(components)),
                )
        elif len(seen) == 2:
            # The vulnerable implementation would accept the restored
            # snapshot and return its original, apparently valid digest.
            if mutation == "local_state":
                object.__setattr__(root, "local_state", ReadinessState.BLOCKED)
            elif mutation == "schema_revision":
                object.__setattr__(root, "schema_revision", None)
            else:
                object.__setattr__(snapshot, "components", components)
        return result

    monkeypatch.setattr(startup, "_identifier", identifying)
    # The existing identifier-validation wrapper preserves its established
    # diagnostic while propagating this fail-closed epoch rejection.
    with pytest.raises(ValueError, match="startup snapshot identifier changed"):
        snapshot.state("child")
    assert len(seen) == 1


def test_json_digest_boundary_rejects_temporary_component_retarget(monkeypatch):
    snapshot = _snapshot()
    root = next(
        item for item in snapshot.components if item.component_id == "root"
    )
    original_dumps = startup.json.dumps
    original_sha = startup.hashlib.sha256
    invoked = {"json": False, "sha": False}

    def dumping(*args, **kwargs):
        value = original_dumps(*args, **kwargs)
        invoked["json"] = True
        object.__setattr__(root, "failure_code", "temporary")
        return value

    def hashing(*args, **kwargs):
        invoked["sha"] = True
        object.__setattr__(root, "failure_code", None)
        return original_sha(*args, **kwargs)

    monkeypatch.setattr(startup.json, "dumps", dumping)
    monkeypatch.setattr(startup.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="startup snapshot changed"):
        snapshot.state("root")
    assert invoked == {"json": True, "sha": False}


def test_unmodified_readiness_still_keeps_blocked_dependency_semantics():
    snapshot = _snapshot()
    assert snapshot.state("root") is ReadinessState.BLOCKED
    assert snapshot.state("child") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("child") == ("root",)
