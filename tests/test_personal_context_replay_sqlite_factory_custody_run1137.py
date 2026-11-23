"""Run1137: Personal Context replay ledger pins its SQLite connection factory."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ark import personal_context_replay_ledger as replay


def test_sqlite_module_binding_substitution_is_denied_before_connect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted SQLite factory must not execute")

    proxy = SimpleNamespace(
        connect=forbidden,
        Connection=replay._ORIGINAL_SQLITE_CONNECTION,
        IntegrityError=replay._ORIGINAL_SQLITE_INTEGRITY_ERROR,
    )
    monkeypatch.setattr(replay, "sqlite3", proxy)

    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay protocol authority changed",
    ):
        replay.DisconnectedContextReplayLedger(tmp_path / "context.sqlite3", create=True)

    assert calls == []


def test_live_sqlite_connect_attribute_substitution_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted SQLite factory must not execute")

    proxy = SimpleNamespace(
        connect=forbidden,
        Connection=replay._ORIGINAL_SQLITE_CONNECTION,
        IntegrityError=replay._ORIGINAL_SQLITE_INTEGRITY_ERROR,
    )
    monkeypatch.setattr(replay, "sqlite3", proxy)
    monkeypatch.setattr(replay, "_ORIGINAL_SQLITE3", proxy)

    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay protocol authority changed",
    ):
        replay._require_original_replay_protocol()

    assert calls == []


def test_captured_sqlite_connect_substitution_is_denied_before_connect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted captured factory must not execute")

    monkeypatch.setattr(replay, "_ORIGINAL_SQLITE_CONNECT", forbidden)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay protocol authority changed",
    ):
        replay.DisconnectedContextReplayLedger(tmp_path / "context.sqlite3", create=True)

    assert calls == []


@pytest.mark.parametrize("target", ("Connection", "IntegrityError"))
def test_sqlite_result_and_error_types_are_pinned(
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    proxy = SimpleNamespace(
        connect=replay._ORIGINAL_SQLITE_CONNECT,
        Connection=object if target == "Connection" else replay._ORIGINAL_SQLITE_CONNECTION,
        IntegrityError=RuntimeError if target == "IntegrityError" else replay._ORIGINAL_SQLITE_INTEGRITY_ERROR,
    )
    monkeypatch.setattr(replay, "sqlite3", proxy)
    monkeypatch.setattr(replay, "_ORIGINAL_SQLITE3", proxy)

    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay protocol authority changed",
    ):
        replay._require_original_replay_protocol()


def test_original_factory_returns_exact_local_sqlite_connection() -> None:
    connection = replay._connect_original(":memory:")
    try:
        assert type(connection) is replay._ORIGINAL_SQLITE_CONNECTION
    finally:
        connection.close()


def test_replay_connection_helper_identity_is_pinned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted connection helper must not execute")

    monkeypatch.setattr(replay, "_connect_original", forbidden)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="context replay protocol authority changed",
    ):
        replay.DisconnectedContextReplayLedger(tmp_path / "context.sqlite3", create=True)

    assert calls == []
