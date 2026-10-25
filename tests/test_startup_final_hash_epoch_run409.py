"""Final hash callbacks cannot rebase disconnected readiness evidence.

These fixtures do not authenticate machine health, real services or any
permission to dispatch an external action.
"""

import pytest

import ark.startup_readiness_review as startup
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize(
    ("target", "field", "replacement"),
    (
        ("root", "local_state", ReadinessState.READY),
        ("root", "schema_revision", "injected-revision"),
        ("child", "dependencies", ()),
        ("root", "failure_code", "injected-failure"),
    ),
)
def test_final_hash_callback_cannot_reclassify_an_original_probe(
    monkeypatch, target, field, replacement,
):
    root = StartupComponent("root", local_state=ReadinessState.BLOCKED)
    child = StartupComponent("child", dependencies=("root",))
    selected = root if target == "root" else child
    original_hash = startup.hashlib.sha256
    entered = []

    def hashing(payload):
        value = original_hash(payload)
        entered.append(True)
        object.__setattr__(selected, field, replacement)
        return value

    monkeypatch.setattr(startup.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="startup input changed"):
        evaluate_startup_readiness((root, child))
    assert entered == [True]


def test_final_hash_cannot_replace_an_equal_valued_dependency_tuple(monkeypatch):
    root = StartupComponent("root", local_state=ReadinessState.BLOCKED)
    child = StartupComponent("child", dependencies=("root",))
    old_dependencies = child.dependencies
    original_hash = startup.hashlib.sha256

    def hashing(payload):
        digest = original_hash(payload)
        object.__setattr__(child, "dependencies", tuple(list(old_dependencies)))
        assert child.dependencies == old_dependencies
        assert child.dependencies is not old_dependencies
        return digest

    monkeypatch.setattr(startup.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="startup input changed"):
        evaluate_startup_readiness((root, child))


def test_cached_snapshot_rejects_equal_value_digest_carrier_replacement(
    monkeypatch,
):
    snapshot = evaluate_startup_readiness((
        StartupComponent("root", local_state=ReadinessState.BLOCKED),
        StartupComponent("child", dependencies=("root",)),
    ))
    original = snapshot.digest
    original_hash = startup.hashlib.sha256

    def hashing(payload):
        digest = original_hash(payload)
        clone = original.encode("ascii").decode("ascii")
        assert clone == original and clone is not original
        object.__setattr__(snapshot, "digest", clone)
        return digest

    monkeypatch.setattr(startup.hashlib, "sha256", hashing)
    with pytest.raises(ValueError, match="startup snapshot changed"):
        snapshot.state("child")


def test_clean_final_hash_keeps_dependency_denial_and_inert_snapshot():
    snapshot = evaluate_startup_readiness((
        StartupComponent("root", local_state=ReadinessState.BLOCKED),
        StartupComponent("child", dependencies=("root",)),
    ))
    assert snapshot.state("root") is ReadinessState.BLOCKED
    assert snapshot.state("child") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("child") == ("root",)
