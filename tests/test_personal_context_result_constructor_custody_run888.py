"""Synthetic context output must not execute replaced constructors/getters.

Disconnected, in-memory Memory fixtures only; no private source, permission,
network, SQLite write or real tool execution.
"""

import hashlib
import subprocess
import sys

import pytest

from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


def _inputs() -> CoherentSnapshotReview:
    scope = MemoryScope("synthetic-owner", "local")
    source = "offline-source"
    content = "offline context row"
    record = MemoryRecord(
        deterministic_memory_id(scope, source), scope, source, content,
        {}, 1, 2, None, 1,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )
    return CoherentSnapshotReview(10, (scope,), ((record,),), "a" * 64)


def _project() -> context.SyntheticContextBundle:
    return context.review_personal_context(
        _inputs(), context.ContextSelectionPolicy(1, 1),
    )


@pytest.mark.parametrize(("carrier", "attribute"), (
    ("item", "__init__"),
    ("bundle", "__init__"),
    ("item", "content"),
    ("bundle", "bundle_id"),
    ("bundle", "action_authorized"),
    ("bundle", "dispatch_authorized"),
))
def test_reflected_context_carrier_never_runs_replacement(
    monkeypatch: pytest.MonkeyPatch, carrier: str, attribute: str,
) -> None:
    target = (
        context.SyntheticContextItem if carrier == "item"
        else context.SyntheticContextBundle
    )
    invoked: list[str] = []

    def adversarial(*_args: object, **_kwargs: object) -> None:
        invoked.append(attribute)
        raise AssertionError("replaced context callback executed")

    replacement = adversarial if attribute == "__init__" else property(adversarial)
    monkeypatch.setattr(target, attribute, replacement)
    with pytest.raises(
        context.PersonalContextReviewRejected, match="context result carrier changed",
    ):
        _project()
    assert invoked == []


@pytest.mark.parametrize("carrier", ("item", "bundle"))
def test_reentrant_hash_cannot_install_synthetic_constructor(
    monkeypatch: pytest.MonkeyPatch, carrier: str,
) -> None:
    target = (
        context.SyntheticContextItem if carrier == "item"
        else context.SyntheticContextBundle
    )
    original_hash = context._hash
    invoked: list[str] = []

    def adversarial(*_args: object, **_kwargs: object) -> None:
        invoked.append(carrier)
        raise AssertionError("replaced constructor executed")

    def replace_after_validation(label: str, payload: object) -> str:
        if not invoked:
            monkeypatch.setattr(target, "__init__", adversarial)
            invoked.append("installed")
        return original_hash(label, payload)

    with monkeypatch.context() as patch:
        patch.setattr(context, "_hash", replace_after_validation)
        with pytest.raises(
            context.PersonalContextReviewRejected,
            match="context result carrier changed",
        ):
            _project()
    assert invoked == ["installed"]


def test_hostile_new_is_isolated_from_other_pytest_cases() -> None:
    probe = """
import hashlib
from ark import personal_context_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id
scope = MemoryScope('synthetic-owner', 'local')
content = 'offline row'
record = MemoryRecord(
    deterministic_memory_id(scope, 'source'), scope, 'source', content,
    {}, 1, 2, None, 1, hashlib.sha256(content.encode()).hexdigest(),
)
snapshot = CoherentSnapshotReview(10, (scope,), ((record,),), 'a' * 64)
executed = []
def hostile(*args, **kwargs):
    executed.append(1)
    raise AssertionError('hostile __new__ called')
context.SyntheticContextBundle.__new__ = hostile
try:
    context.review_personal_context(snapshot, context.ContextSelectionPolicy(1, 1))
except context.PersonalContextReviewRejected as exc:
    assert 'context result carrier changed' in str(exc)
else:
    raise AssertionError('hostile constructor accepted')
assert not executed
"""
    child = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert child.returncode == 0, child.stderr


def test_unmodified_context_outputs_remain_non_authorizing() -> None:
    result = _project()
    assert len(result.items) == 1
    assert result.items[0].content == "offline context row"
    assert result.action_authorized is False
    assert result.dispatch_authorized is False
