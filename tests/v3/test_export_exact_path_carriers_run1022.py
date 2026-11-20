"""Run1022: export path admission rejects caller-owned PathLike callbacks."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning import export_plan as module
from ark.learning.export_plan import _validate_export_output_path


class CallbackPath(type(Path("."))):
    def __init__(self, *parts):
        super().__init__()
        self._callback_parts = parts

    def __fspath__(self):
        raise AssertionError("untrusted PathLike __fspath__ must not run")


def _inputs(tmp_path):
    base = tmp_path / "base-model"
    merged = tmp_path / "merged-candidate"
    base.mkdir()
    merged.mkdir()
    return {
        "output_dir": tmp_path / "export",
        "base_dir": base,
        "merged_candidate_dir": merged,
        "current_model_path": None,
    }


@pytest.mark.parametrize("target", (
    "output_dir", "base_dir", "merged_candidate_dir", "current_model_path",
))
def test_export_pathlike_subclass_is_rejected_before_fspath(tmp_path, target):
    values = _inputs(tmp_path)
    values[target] = CallbackPath("/synthetic/untrusted")
    with pytest.raises(ValueError, match="exact native Path"):
        _validate_export_output_path(**values)


@pytest.mark.parametrize("target", ("converter_path", "quantizer_path"))
def test_build_export_plan_rejects_tool_pathlike_before_snapshot_validation(
    tmp_path, monkeypatch, target,
):
    values = {
        "base_dir": tmp_path,
        "merged_candidate_dir": tmp_path,
        "converter_path": tmp_path / "converter",
        "quantizer_path": tmp_path / "quantizer",
        "output_dir": tmp_path / "export",
    }
    values[target] = CallbackPath("/synthetic/untrusted")
    validation_calls = []

    def forbidden_validation(*_args, **_kwargs):
        validation_calls.append("snapshot")
        raise AssertionError("path admission must precede snapshot processing")

    monkeypatch.setattr(module, "validate_experiment_001", forbidden_validation)
    with pytest.raises(ValueError, match="exact native Path"):
        module.build_export_plan({}, **values)
    assert validation_calls == []


def test_exact_native_paths_keep_validation_only_output_behavior(tmp_path):
    values = _inputs(tmp_path)
    assert _validate_export_output_path(**values) is None
    assert not values["output_dir"].exists()
