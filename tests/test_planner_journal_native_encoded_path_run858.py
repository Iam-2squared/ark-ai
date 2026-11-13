"""Portable, read-only path admission regressions for synthetic Planner journals.

The journal is a fixture and never authorizes dispatch or replay.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency import planner_journal_review as journal


@pytest.mark.parametrize("kind", ("multibyte", "nul", "root"))
def test_invalid_journal_paths_rejected_before_filesystem_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kind: str,
) -> None:
    if kind == "multibyte":
        source = tmp_path / ("界" * 1400 + ".sqlite3")
        assert len(str(source)) < 4096
        assert len(os.fsencode(source)) + len(b"-journal") > 4096
    elif kind == "nul":
        source = tmp_path / "bad\x00name.sqlite3"
    else:
        source = Path(tmp_path.anchor)

    def forbid_lstat(_self: Path) -> object:
        raise AssertionError("invalid Planner path reached filesystem inventory")

    with monkeypatch.context() as patched:
        patched.setattr(Path, "lstat", forbid_lstat)
        with pytest.raises(
            journal.SyntheticPlanJournalRejected,
            match="absolute non-traversing Path",
        ):
            journal._require_safe_journal_path(source)


def test_safe_native_absolute_fixture_path_is_accepted(tmp_path: Path) -> None:
    source = tmp_path / "safe.sqlite3"
    assert source.is_absolute()
    journal._require_safe_journal_path(source)
