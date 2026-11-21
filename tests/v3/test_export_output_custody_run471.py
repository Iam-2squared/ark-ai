"""Free-only export plan path fences; no converter or GPU ever executed."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning import export_plan as module
from ark.learning.export_plan import _validate_export_output_path


def _inputs(tmp_path):
    base = tmp_path / "base-model"
    merged = tmp_path / "merged-candidate"
    base.mkdir()
    merged.mkdir()
    return base, merged, tmp_path / "export"


def _check(output, base, merged, *, model=None):
    return _validate_export_output_path(
        output, base_dir=base, merged_candidate_dir=merged,
        current_model_path=model,
    )


def test_new_sibling_export_destination_is_validation_only(tmp_path):
    base, merged, output = _inputs(tmp_path)
    _check(output, base, merged)
    assert not output.exists()


@pytest.mark.parametrize("kind", (
    "inside-base", "inside-merged", "existing", "missing-parent", "traversal",
))
def test_export_rejects_unsafe_output_leaf_or_overlap(tmp_path, kind):
    base, merged, output = _inputs(tmp_path)
    inside_base = base / "export"
    inside_merged = merged / "export"
    existing = tmp_path / "existing"
    existing.mkdir()
    paths = {
        "inside-base": inside_base,
        "inside-merged": inside_merged,
        "existing": existing,
        "missing-parent": tmp_path / "missing" / "export",
        "traversal": base / ".." / "export",
    }
    with pytest.raises(ValueError, match="export output"):
        _check(paths[kind], base, merged)
    assert not output.exists()


def test_export_rejects_symlinked_parent(tmp_path):
    base, merged, output = _inputs(tmp_path)
    link = tmp_path / "alias"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks not permitted on this OS")
    with pytest.raises(ValueError, match="export output"):
        _check(link / output.name, base, merged)
    assert not output.exists()


@pytest.mark.parametrize("name", (
    "paired-current-f16.gguf", "paired-current-Q4_K_M.gguf",
    "candidate-f16.gguf", "candidate-Q4_K_M.gguf",
))
def test_export_rejects_normalized_deployed_model_collision(tmp_path, name):
    base, merged, output = _inputs(tmp_path)
    # A textual path inequality cannot evade the canonical output-file fence.
    equivalent = base / ".." / output.name / name
    assert equivalent != output / name
    with pytest.raises(ValueError, match="deployed model"):
        _check(output, base, merged, model=equivalent)
    assert not output.exists()


def test_export_overlap_rejected_before_tool_hash_or_subprocess(tmp_path, monkeypatch):
    base, merged, _ = _inputs(tmp_path)

    monkeypatch.setattr(
        module, "validate_experiment_001",
        lambda snapshot, authorization_scope: "a" * 64,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("unsafe output must be rejected before tool hashing")

    monkeypatch.setattr(module, "build_tool_identity", forbidden)
    with pytest.raises(ValueError, match="protected input tree"):
        module.build_export_plan(
            {}, base_dir=base, merged_candidate_dir=merged,
            converter_path=Path("missing-converter"),
            quantizer_path=Path("missing-quantizer"),
            output_dir=base / "export",
        )
    assert not (base / "export").exists()
