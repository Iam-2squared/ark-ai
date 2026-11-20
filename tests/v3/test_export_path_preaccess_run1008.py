"""Run1008: exact export path carriers and no-follow output admission."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import ark.learning.export_plan as module
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


@pytest.mark.parametrize("position", ("output", "base", "candidate", "model"))
def test_export_rejects_path_subclasses_before_fspath_callbacks(
    tmp_path: Path, position: str,
) -> None:
    base, candidate, output = _roots(tmp_path)
    callbacks: list[str] = []

    class CallbackPath(type(Path("."))):
        def __fspath__(self):
            callbacks.append("fspath")
            return super().__fspath__()

    source = {
        "output": output,
        "base": base,
        "candidate": candidate,
        "model": tmp_path / "deployed.gguf",
    }[position]
    wrapped = CallbackPath(str(source))
    arguments = {
        "output_dir": output,
        "base_dir": base,
        "merged_candidate_dir": candidate,
        "current_model_path": None,
    }
    if position == "output":
        arguments["output"] = wrapped
    elif position == "base":
        arguments["base_dir"] = wrapped
    elif position == "candidate":
        arguments["merged_candidate_dir"] = wrapped
    else:
        arguments["current_model_path"] = wrapped

    with pytest.raises(ValueError, match="exact local pathlib.Path"):
        _validate_export_output_path(**arguments)
    assert callbacks == []


def test_build_export_plan_rejects_converter_path_subclass_before_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, candidate, output = _roots(tmp_path)
    calls: list[str] = []

    class CallbackPath(type(Path("."))):
        def __fspath__(self):
            calls.append("fspath")
            return super().__fspath__()

    def forbidden_snapshot(*args, **kwargs):
        pytest.fail("snapshot validation ran before exact path admission")

    monkeypatch.setattr(module, "validate_experiment_001", forbidden_snapshot)
    with pytest.raises(ValueError, match="exact local pathlib.Path"):
        module.build_export_plan(
            {},
            base_dir=base,
            merged_candidate_dir=candidate,
            converter_path=CallbackPath("converter.py"),
            quantizer_path=Path("quantizer"),
            output_dir=output,
        )
    assert calls == []


def test_export_rejects_multibyte_native_path_over_budget_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, candidate, _ = _roots(tmp_path)
    output = tmp_path / ("🙂" * 1100) / "export"
    assert len(str(output)) < 4096
    assert len(os.fsencode(output)) > 4096

    def forbidden_lstat(_path):
        pytest.fail("filesystem access occurred before native path byte admission")

    monkeypatch.setattr(type(Path(".")), "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="native byte budget"):
        _check(output, base, candidate)


def test_symlinked_output_ancestor_is_rejected_before_leaf_following_probes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, candidate, _ = _roots(tmp_path)
    alias = tmp_path / "output-alias"
    try:
        alias.symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are not permitted on this OS")
    output = alias / "export"

    def forbidden(_path):
        pytest.fail("output leaf was probed before its ancestors were admitted")

    monkeypatch.setattr(type(Path(".")), "exists", forbidden)
    monkeypatch.setattr(type(Path(".")), "is_symlink", forbidden)
    with pytest.raises(ValueError, match="export output"):
        _check(output, base, candidate)


def test_dangling_output_symlink_is_rejected_by_leaf_lstat(tmp_path: Path) -> None:
    base, candidate, output = _roots(tmp_path)
    output.symlink_to(tmp_path / "missing-export-target", target_is_directory=True)
    with pytest.raises(ValueError, match="export output"):
        _check(output, base, candidate)
    assert not (tmp_path / "missing-export-target").exists()
