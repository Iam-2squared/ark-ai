"""Reject hostile or unbounded Memory scope input before private attribute access."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import coherent_expiry_restart_bridge as bridge
from ark.memory.coherent_expiry_snapshot_review import review_coherent_expiry_snapshot


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory-scope-entry.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("owner", "notes")
    store.put(MemoryWrite(scope, "a", "private", expires_at_ms=1200))
    retained = review_coherent_expiry_snapshot(store, (scope,), now_ms=1500)
    return store, scope, retained


def test_exact_scope_still_produces_inert_manual_review(tmp_path) -> None:
    store, scope, retained = _case(tmp_path)
    result = bridge.review_coherent_expiry_restart(
        store, (scope,), retained, now_ms=1500,
    )
    assert result.transition == "UNCHANGED_LOCAL_CLAIM"
    assert result.automatic_purge_authorized is False
    assert result.independent_custody_verified is False
    assert "private" not in repr(result)


def test_hostile_foreign_scope_refused_before_getters_and_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _, retained = _case(tmp_path)
    calls = []

    class HostileScope:
        @property
        def owner_id(self):
            calls.append("owner")
            raise AssertionError("untrusted scope getter executed")

        @property
        def namespace(self):
            calls.append("namespace")
            raise AssertionError("untrusted namespace getter executed")

    def no_sqlite():
        calls.append("sqlite")
        raise AssertionError("invalid scope reached SQLite")

    monkeypatch.setattr(store, "_connect_readonly", no_sqlite)
    with pytest.raises(
        bridge.CoherentExpiryRestartRejected,
        match="inexact coherent restart inputs",
    ):
        bridge.review_coherent_expiry_restart(
            store, (HostileScope(),), retained, now_ms=1500,
        )
    assert calls == []


@pytest.mark.parametrize("size", (0, 17))
def test_empty_or_oversized_scope_tuple_refused_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, size: int,
) -> None:
    store, scope, retained = _case(tmp_path)
    calls = []

    def no_sqlite():
        calls.append("sqlite")
        raise AssertionError("invalid scope inventory reached SQLite")

    monkeypatch.setattr(store, "_connect_readonly", no_sqlite)
    with pytest.raises(
        bridge.CoherentExpiryRestartRejected,
        match="inexact coherent restart inputs",
    ):
        bridge.review_coherent_expiry_restart(
            store, (scope,) * size, retained, now_ms=1500,
        )
    assert calls == []


@pytest.mark.parametrize(
    ("clock", "limit"),
    (
        (-1, 100),
        (2**63, 100),
        (True, 100),
        (1500, 0),
        (1500, 101),
        (1500, True),
    ),
)
def test_invalid_clock_or_page_budget_refused_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
    clock: int, limit: int,
) -> None:
    store, scope, retained = _case(tmp_path)
    calls = []

    def no_sqlite():
        calls.append("sqlite")
        raise AssertionError("invalid clock or budget reached SQLite")

    monkeypatch.setattr(store, "_connect_readonly", no_sqlite)
    with pytest.raises(
        bridge.CoherentExpiryRestartRejected,
        match="inexact coherent restart inputs",
    ):
        bridge.review_coherent_expiry_restart(
            store, (scope,), retained, now_ms=clock, limit=limit,
        )
    assert calls == []
