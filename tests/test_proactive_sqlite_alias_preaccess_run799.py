"""Disconnected proactive SQLite refuses known file/sidecar/path aliases.

Only local fixture file metadata is checked. There is no scheduler service,
notification, credential, real ToolBackend or trusted execution clock.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _symlink(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"platform cannot create synthetic symlink: {exc}")


def _prepare(ledger: SyntheticProactiveLedger) -> None:
    ledger.prepare(
        SyntheticTriggerPolicy(
            "owner", "offline", "alias-check", 1, "v1", 1, 100, 3,
        ),
        source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=10,
        now_ms=10,
    )


@pytest.mark.parametrize("operation", ("initialize", "count", "prepare"))
def test_symbolic_main_database_path_refused(tmp_path, operation):
    main = tmp_path / "main.sqlite3"
    ledger = SyntheticProactiveLedger(main)
    link = tmp_path / "alias.sqlite3"
    _symlink(link, main)
    if operation == "initialize":
        with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive"):
            SyntheticProactiveLedger(link)
    elif operation == "count":
        ledger.path = link
        with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive"):
            ledger.count()
    else:
        ledger.path = link
        with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive"):
            _prepare(ledger)
    assert SyntheticProactiveLedger(main).count() == 0


def test_hardlinked_main_database_refused(tmp_path):
    main = tmp_path / "main.sqlite3"
    ledger = SyntheticProactiveLedger(main)
    link = tmp_path / "hardlink.sqlite3"
    try:
        link.hardlink_to(main)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"platform cannot create synthetic hardlink: {exc}")
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite file"):
        ledger.count()
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite file"):
        _prepare(ledger)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_symbolic_sqlite_sidecar_refused(tmp_path, suffix):
    main = tmp_path / "main.sqlite3"
    ledger = SyntheticProactiveLedger(main)
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("synthetic", encoding="utf-8")
    _symlink(tmp_path / ("main.sqlite3" + suffix), unrelated)
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite sidecar"):
        ledger.count()
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite sidecar"):
        _prepare(ledger)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_orphan_regular_sidecar_cannot_be_adopted_on_create(tmp_path, suffix):
    main = tmp_path / "new.sqlite3"
    sidecar = tmp_path / ("new.sqlite3" + suffix)
    sidecar.write_bytes(b"orphan")
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite sidecar"):
        SyntheticProactiveLedger(main)
    assert not main.exists()
    assert sidecar.read_bytes() == b"orphan"


def test_symlink_directory_parent_refused(tmp_path):
    real = tmp_path / "private"
    real.mkdir()
    link = tmp_path / "alias-dir"
    _symlink(link, real)
    target = link / "would-create.sqlite3"
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive parent path"):
        SyntheticProactiveLedger(target)
    assert not (real / "would-create.sqlite3").exists()


def test_regular_fixture_still_prepares_only_inert_marker(tmp_path):
    main = tmp_path / "regular.sqlite3"
    ledger = SyntheticProactiveLedger(main)
    _prepare(ledger)
    assert ledger.count() == 1
    assert SyntheticProactiveLedger(main).count() == 1
