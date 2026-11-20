"""Run1017: export path guards reject a rebound concrete pathlib type."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.learning.export_plan as export_plan


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    base = tmp_path / "base-model"
    candidate = tmp_path / "merged-candidate"
    base.mkdir()
    candidate.mkdir()
    return base, candidate, tmp_path / "export"


def test_export_rejects_rebound_original_path_type_before_subclass_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, candidate, output = _roots(tmp_path)
    calls: list[str] = []
    original_type = type(Path("."))

    class ReboundPath(original_type):
        def __getattribute__(self, name: str):
            if name == "parts":
                calls.append(name)
                raise AssertionError("subclass path hook executed before admission")
            return super().__getattribute__(name)

    rebound = ReboundPath(output)
    assert type(rebound) is ReboundPath

    with monkeypatch.context() as scoped:
        # The old codec guard accepted this coordinated type rebind because
        # the subclass inherited the original __fspath__ descriptor.
        scoped.setattr(export_plan, "_ORIGINAL_PATH_TYPE", ReboundPath)
        with pytest.raises(
            ValueError, match="path inspection dependencies changed",
        ):
            export_plan._validate_export_output_path(
                rebound,
                base_dir=base,
                merged_candidate_dir=candidate,
                current_model_path=None,
            )
    assert calls == []
    assert not output.exists()
