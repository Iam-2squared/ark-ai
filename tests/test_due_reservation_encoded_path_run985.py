"""No filesystem/SQLite access for malformed synthetic due ledger paths.

Only disposable local fixture paths are exercised. No trusted clock,
notification, actual scheduler, or tool execution is authorized.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency import disconnected_due_reservation as due


@pytest.mark.parametrize(
    ("tail", "expected"),
    (
        ("界" * 1400 + ".db", "byte budget"),
        ("invalid-\\ud800.db", "encoding"),
        ("native\\x00separator.db", "byte budget"),
    ),
)
def test_due_rejects_unusable_fixture_path_before_lstat(
    tmp_path: Path, monkeypatch, tail: str, expected: str,
) -> None:
    # Never allow a path probe when the input's encoded form is invalid,
    # even if the lexical code-point length fits the old 4096 cap.
    observed: list[Path] = []

    def forbidden_lstat(self, *args, **kwargs):
        observed.append(self)
        raise AssertionError("unexpected local filesystem access")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(due.DueReservationRejected, match=expected):
            due.DisconnectedDueReservations(tmp_path / tail)
    assert observed == []


def test_due_rejects_overlong_journal_suffix_before_filesystem(
    tmp_path: Path, monkeypatch,
) -> None:
    prefix = len(os.fsencode(tmp_path)) + 1
    length = 4096 - prefix - len(b"-journal") + 1
    assert length > 0
    path = tmp_path / ("a" * length)
    assert len(os.fsencode(path)) <= 4096
    assert len(os.fsencode(path)) + len(b"-journal") > 4096
    observed = []

    def forbidden_lstat(self, *args, **kwargs):
        observed.append(self)
        raise AssertionError("path inspection before sidecar byte budget")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(due.DueReservationRejected, match="byte budget"):
            due._check_path(path, exists=False)
    assert observed == []


def test_due_accepts_normal_multilingual_local_fixture(tmp_path: Path) -> None:
    parent = tmp_path / "日本語データ"
    parent.mkdir()
    store = due.DisconnectedDueReservations(parent / "予定.sqlite")
    assert store.witness() == due.genesis_due_witness()


def test_due_fsencoding_dependency_replacement_denied_before_path_access(
    tmp_path: Path, monkeypatch,
) -> None:
    seen = []

    def unexpected(*args, **kwargs):
        seen.append(args)
        raise AssertionError("untrusted encoding executed")

    with monkeypatch.context() as patch:
        patch.setattr(due.os, "fsencode", unexpected)
        with pytest.raises(
            due.DueReservationRejected, match="digest callback authority",
        ):
            due._check_path(tmp_path / "offline.db", exists=False)
    assert seen == []
