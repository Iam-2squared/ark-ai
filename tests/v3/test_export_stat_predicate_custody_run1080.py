"""V3 export path classification pins its import-original stat predicates."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import export_plan


def _forbidden(*_args, **_kwargs):
    raise AssertionError("filesystem inspection ran before stat-policy admission")


def _paths(tmp_path: Path):
    base = tmp_path / "base-model"
    merged = tmp_path / "merged-candidate"
    base.mkdir()
    merged.mkdir()
    return base, merged, tmp_path / "export"


def test_stat_module_rebinding_is_rejected_before_lstat(tmp_path, monkeypatch):
    base, merged, output = _paths(tmp_path)
    monkeypatch.setattr(Path, "lstat", _forbidden)
    monkeypatch.setattr(
        export_plan,
        "stat",
        SimpleNamespace(S_ISDIR=_forbidden, S_ISLNK=_forbidden, S_ISREG=_forbidden),
    )
    with pytest.raises(ValueError, match="stat predicates changed"):
        export_plan._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=None,
        )


@pytest.mark.parametrize("predicate", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_rebinding_is_rejected_before_lstat(
    predicate, tmp_path, monkeypatch,
):
    base, merged, output = _paths(tmp_path)
    monkeypatch.setattr(Path, "lstat", _forbidden)
    monkeypatch.setattr(export_plan.stat, predicate, _forbidden)
    with pytest.raises(ValueError, match="stat predicates changed"):
        export_plan._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=None,
        )


def test_mode_metadata_callback_cannot_replace_directory_predicate(
    tmp_path, monkeypatch,
):
    base = tmp_path / "base-model"
    base.mkdir()
    original_lstat = Path.lstat

    class Metadata:
        st_file_attributes = 0

        @property
        def st_mode(self):
            monkeypatch.setattr(export_plan.stat, "S_ISDIR", _forbidden)
            return stat.S_IFDIR | 0o755

    def lstat(path):
        if path == base:
            return Metadata()
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="stat predicates changed"):
        export_plan._canonical_existing_directory(base, "base_dir")


def test_reparse_metadata_callback_cannot_replace_symlink_predicate(monkeypatch):
    class Metadata:
        st_file_attributes = 0

        @property
        def st_mode(self):
            monkeypatch.setattr(export_plan.stat, "S_ISLNK", _forbidden)
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="stat predicates changed"):
        export_plan._is_reparse_point(Metadata())
