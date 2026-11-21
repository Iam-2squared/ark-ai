"""Run1047: V3 executable argv identity rejects Unicode formatting controls.

Validation-only path and synthetic strings; no subprocess or converter is run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.learning.export_plan as export_plan
from ark.learning.export_plan import build_export_plan


@pytest.mark.parametrize(
    "control",
    (
        "\u0085", "\u009f", "\u061c", "\u200b", "\u200d",
        "\u2028", "\u2029", "\u202e", "\u2066", "\u2060",
        "\u00ad", "\ufeff",
    ),
)
def test_unicode_formatting_control_is_rejected_before_snapshot_or_path_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, control: str,
) -> None:
    callbacks: list[str] = []

    def forbidden(*_args, **_kwargs):
        callbacks.append("access")
        raise AssertionError("executable admission must precede snapshot/path access")

    with monkeypatch.context() as patch:
        patch.setattr(export_plan, "validate_experiment_001", forbidden)
        patch.setattr(export_plan, "build_tool_identity", forbidden)
        patch.setattr(Path, "lstat", forbidden)
        with pytest.raises(ValueError, match="Unicode formatting control"):
            build_export_plan(
                {},
                base_dir=tmp_path / "base",
                merged_candidate_dir=tmp_path / "merged",
                converter_path=tmp_path / "converter",
                quantizer_path=tmp_path / "quantizer",
                output_dir=tmp_path / "out",
                python_executable=f"python{control}.exe",
            )

    assert callbacks == []


def test_normal_multilingual_executable_path_is_preserved_verbatim() -> None:
    executable = r"C:\Python\日本語\python.exe"
    assert export_plan._require_python_executable(executable) is executable
