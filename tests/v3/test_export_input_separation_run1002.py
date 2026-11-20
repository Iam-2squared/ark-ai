"""Free-only V3 export source separation; no converter or GPU is executed."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning.export_plan import _validate_export_output_path


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    base = tmp_path / "base-model"
    candidate = tmp_path / "merged-candidate"
    base.mkdir()
    candidate.mkdir()
    return base, candidate, tmp_path / "export"


def _check(
    output: Path,
    base: Path,
    candidate: Path,
    *,
    current_model: Path | None = None,
) -> None:
    _validate_export_output_path(
        output,
        base_dir=base,
        merged_candidate_dir=candidate,
        current_model_path=current_model,
    )


@pytest.mark.parametrize("layout", ("same", "candidate-under-base", "base-under-candidate"))
def test_export_rejects_same_or_nested_source_trees(tmp_path: Path, layout: str) -> None:
    base, candidate, output = _roots(tmp_path)
    if layout == "same":
        candidate = base
    elif layout == "candidate-under-base":
        candidate = base / "merged-candidate"
        candidate.mkdir()
    else:
        base = candidate / "base-model"
        base.mkdir()

    with pytest.raises(ValueError, match="distinct and non-overlapping"):
        _check(output, base, candidate)
    assert not output.exists()


def test_export_rejects_lexical_parent_alias_for_source_root(tmp_path: Path) -> None:
    base, candidate, output = _roots(tmp_path)
    aliased_base = base.parent / "unused" / ".." / base.name

    with pytest.raises(ValueError, match="non-aliased local directory"):
        _check(output, aliased_base, candidate)
    assert not output.exists()


def test_export_rejects_symlinked_candidate_root(tmp_path: Path) -> None:
    base, candidate, output = _roots(tmp_path)
    alias = tmp_path / "candidate-alias"
    try:
        alias.symlink_to(candidate, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are not permitted on this OS")

    with pytest.raises(ValueError, match="non-aliased local directory"):
        _check(output, base, alias)
    assert not output.exists()


def test_export_rejects_current_model_inside_candidate_source(tmp_path: Path) -> None:
    base, candidate, output = _roots(tmp_path)
    deployed = candidate / "current.gguf"
    deployed.write_bytes(b"synthetic deployed model marker")

    with pytest.raises(ValueError, match="Candidate source overlaps Current deployed model"):
        _check(output, base, candidate, current_model=deployed)
    assert not output.exists()


def test_export_rejects_lexical_alias_to_current_model_inside_candidate(tmp_path: Path) -> None:
    base, candidate, output = _roots(tmp_path)
    deployed = candidate / "current.gguf"
    deployed.write_bytes(b"synthetic deployed model marker")
    alias = candidate / "unused" / ".." / deployed.name

    with pytest.raises(ValueError, match="Candidate source overlaps Current deployed model"):
        _check(output, base, candidate, current_model=alias)
    assert not output.exists()
