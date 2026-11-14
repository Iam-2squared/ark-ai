"""Retained expiry ordering must not call a poisoned dataclass comparison.

These reviews are local, read-only and never authorize purging private memory.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import coherent_expiry_restart_bridge as bridge
from ark.memory.coherent_expiry_snapshot_review import review_coherent_expiry_snapshot


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scopes = (MemoryScope("owner", "notes"), MemoryScope("owner", "tasks"))
    for scope, source in zip(scopes, ("a", "b"), strict=True):
        store.put(MemoryWrite(scope, source, "private", expires_at_ms=1200))
    prior = review_coherent_expiry_snapshot(store, scopes, now_ms=1500)
    return store, scopes, prior


def test_ordered_retained_pages_remain_inert(tmp_path) -> None:
    store, scopes, prior = _fixture(tmp_path)
    result = bridge.review_coherent_expiry_restart(
        store, scopes, prior, now_ms=1500,
    )
    assert result.transition == "UNCHANGED_LOCAL_CLAIM"
    assert result.automatic_purge_authorized is False


def test_reordered_pages_do_not_execute_poisoned_dataclass_equality(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, scopes, prior = _fixture(tmp_path)
    object.__setattr__(prior, "pages", tuple(reversed(prior.pages)))
    invoked = []

    def forbidden(_self, _other):
        invoked.append("equality")
        raise AssertionError("retained page equality executed")

    monkeypatch.setattr(type(prior.pages[0]), "__eq__", forbidden)
    with pytest.raises(
        bridge.CoherentExpiryRestartRejected, match="pages out of order",
    ):
        bridge.review_coherent_expiry_restart(
            store, scopes, prior, now_ms=1500,
        )
    assert invoked == []


@pytest.mark.parametrize("carrier", ("page", "cohort"))
def test_untrusted_scope_hash_carrier_refused_before_comparison(
    tmp_path, carrier: str,
) -> None:
    store, scopes, prior = _fixture(tmp_path)
    invoked = []

    class HostileHash:
        def __eq__(self, _other):
            invoked.append("equality")
            raise AssertionError("untrusted equality called")

        def __lt__(self, _other):
            invoked.append("ordering")
            raise AssertionError("untrusted ordering called")

    if carrier == "page":
        object.__setattr__(prior.pages[0], "scope_sha256", HostileHash())
    else:
        object.__setattr__(prior.cohort, "scope_hashes", HostileHash())

    with pytest.raises(
        bridge.CoherentExpiryRestartRejected,
        match="invalid prior expiry scope hashes",
    ):
        bridge.review_coherent_expiry_restart(
            store, scopes, prior, now_ms=1500,
        )
    assert invoked == []
