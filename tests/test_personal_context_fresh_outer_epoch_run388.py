"""Fresh context must keep the same sources and policy across veto checks.

This projection is a disconnected fixture; it never grants data use authority.
"""

from pathlib import Path

import pytest

import ark.personal_context_revocation_continuity_review as continuity_module
import ark.personal_context_revocation_review as module
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _fixture(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory # %.sqlite", clock_ms=lambda: 100)
    memory.put(MemoryWrite(
        MemoryScope("fixture-owner", "private"), "name", "PRIVATE-CONTENT",
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    request = CoherentSnapshotRequest("fixture-owner", ("private",))
    policy = ContextSelectionPolicy(2, 2)
    return memory, veto, request, policy


def _review(state):
    return module.review_fresh_nonrevoked_context(
        state[0], state[2], state[3], state[1],
    )


@pytest.mark.parametrize("hook", ["review_coherent_snapshot", "review_personal_context"])
def test_memory_source_redirected_after_inner_read_is_denied(
    tmp_path: Path, monkeypatch, hook: str,
):
    state = _fixture(tmp_path)
    original = getattr(module, hook)

    def redirected(*args, **kwargs):
        result = original(*args, **kwargs)
        state[0].path = Path(str(state[0].path))
        return result

    monkeypatch.setattr(module, hook, redirected)
    with pytest.raises(SyntheticContextRevocationRejected, match="source"):
        _review(state)


@pytest.mark.parametrize("after_continuity", [1, 2])
def test_veto_source_redirected_across_read_passes_is_denied(
    tmp_path: Path, monkeypatch, after_continuity: int,
):
    state = _fixture(tmp_path)
    original = continuity_module.review_revocation_continuity
    calls = 0

    def redirected(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == after_continuity:
            state[1].path = Path(str(state[1].path))
        return result

    monkeypatch.setattr(continuity_module, "review_revocation_continuity", redirected)
    with pytest.raises(SyntheticContextRevocationRejected, match="source"):
        _review(state)
    assert calls == after_continuity


@pytest.mark.parametrize("hook", ["review_personal_context", "review_coherent_snapshot"])
def test_policy_swap_after_callback_is_denied(tmp_path: Path, monkeypatch, hook: str):
    state = _fixture(tmp_path)
    original = getattr(module, hook)

    def mutate_policy(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(state[3], "total_limit", 3)
        return result

    monkeypatch.setattr(module, hook, mutate_policy)
    with pytest.raises(SyntheticContextRevocationRejected, match="policy"):
        _review(state)


def test_stable_context_projection_remains_non_authorizing(tmp_path: Path):
    bundle = _review(_fixture(tmp_path))
    assert len(bundle.items) == 1
    assert bundle.action_authorized is False
    assert bundle.dispatch_authorized is False
