"""Run1393: export stat policy retains its complete import-time vector epoch."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import export_plan


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    base = tmp_path / "base-model"
    merged = tmp_path / "merged-candidate"
    base.mkdir()
    merged.mkdir()
    return base, merged, tmp_path / "export"


def _replace_all_stat_aliases(
    monkeypatch: pytest.MonkeyPatch,
    predicate_calls: list[str],
) -> None:
    def hostile(name: str):
        def reject(*_args: object, **_kwargs: object) -> bool:
            predicate_calls.append(name)
            raise AssertionError("replacement stat predicate executed")

        return reject

    is_dir = hostile("S_ISDIR")
    is_link = hostile("S_ISLNK")
    is_regular = hostile("S_ISREG")
    fake_stat = SimpleNamespace(
        S_ISDIR=is_dir,
        S_ISLNK=is_link,
        S_ISREG=is_regular,
    )
    forged_epoch = (fake_stat, is_dir, is_link, is_regular)
    monkeypatch.setattr(export_plan, "stat", fake_stat)
    monkeypatch.setattr(export_plan, "_ORIGINAL_STAT", fake_stat)
    monkeypatch.setattr(export_plan, "_ORIGINAL_STAT_S_ISDIR", is_dir)
    monkeypatch.setattr(export_plan, "_ORIGINAL_STAT_S_ISLNK", is_link)
    monkeypatch.setattr(export_plan, "_ORIGINAL_STAT_S_ISREG", is_regular)
    monkeypatch.setattr(export_plan, "_ORIGINAL_STAT_POLICY_EPOCH", forged_epoch)


def test_joint_stat_alias_and_epoch_replacement_is_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, merged, output = _paths(tmp_path)
    predicate_calls: list[str] = []
    _replace_all_stat_aliases(monkeypatch, predicate_calls)

    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspection ran before stat-policy denial")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="stat predicates changed"):
        export_plan._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=None,
        )

    assert predicate_calls == []


def test_joint_stat_alias_and_epoch_replacement_during_lstat_is_denied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, merged, output = _paths(tmp_path)
    original_lstat = Path.lstat
    predicate_calls: list[str] = []

    def lstat(path: Path):
        if path == tmp_path:
            _replace_all_stat_aliases(monkeypatch, predicate_calls)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="stat predicates changed"):
        export_plan._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=None,
        )

    assert predicate_calls == []
