"""Run1372: durable occurrence path-policy guard self-custody."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.agency.durable_occurrence_review as occurrence
from ark.agency.durable_occurrence_review import SyntheticReplayRejected


def test_replaced_occurrence_path_guard_is_rejected_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lstat_calls: list[Path] = []

    def forbidden_lstat(path: Path):
        lstat_calls.append(path)
        raise AssertionError("filesystem inspected after path guard replacement")

    with monkeypatch.context() as patch:
        patch.setattr(
            occurrence, "_require_original_occurrence_path_policy", lambda: None,
        )
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            SyntheticReplayRejected,
            match="synthetic occurrence path policy changed",
        ):
            occurrence._require_safe_occurrence_path(
                tmp_path / "occurrence.sqlite3", create=True,
            )

    assert lstat_calls == []


def test_reentrant_occurrence_path_guard_replacement_is_rejected_after_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    lstat_calls: list[Path] = []

    def replace_guard_after_lstat(path: Path):
        lstat_calls.append(path)
        metadata = original_lstat(path)
        patch.setattr(
            occurrence, "_require_original_occurrence_path_policy", lambda: None,
        )
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", replace_guard_after_lstat)
        with pytest.raises(
            SyntheticReplayRejected,
            match="synthetic occurrence path policy changed",
        ):
            occurrence._require_safe_occurrence_path(
                tmp_path / "occurrence.sqlite3", create=True,
            )

    assert len(lstat_calls) == 1
