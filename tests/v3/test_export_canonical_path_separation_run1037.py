"""Canonical V3 export path separation; no converter, quantizer or GPU is run."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import export_plan as module


def _paths(tmp_path: Path):
    base = tmp_path / "base-model"
    merged = tmp_path / "merged-candidate"
    base.mkdir()
    merged.mkdir()
    converter = tmp_path / "convert_hf_to_gguf.py"
    quantizer = tmp_path / "llama-quantize"
    converter.write_text("# synthetic converter identity", encoding="utf-8")
    quantizer.write_bytes(b"synthetic quantizer identity")
    return base, merged, converter, quantizer, tmp_path / "export"


def _canonicalize(base, merged, output, *, converter=None, quantizer=None, current=None):
    return module._canonicalize_export_paths(
        base_dir=base,
        merged_candidate_dir=merged,
        output_dir=output,
        converter_path=converter,
        quantizer_path=quantizer,
        current_model_path=current,
    )


def test_export_output_inside_repository_source_tree_is_rejected(tmp_path):
    base, merged, _, _, _ = _paths(tmp_path)
    output = module._SOURCE_TREE_ROOT / f".ark-export-test-{tmp_path.name}"
    assert not output.exists()

    with pytest.raises(ValueError, match="protected input tree"):
        module._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=None,
        )

    assert not output.exists()


def test_base_and_candidate_source_roots_must_be_disjoint(tmp_path):
    base, _, _, _, output = _paths(tmp_path)

    with pytest.raises(ValueError, match="canonically separated"):
        _canonicalize(base, base, output)


def test_nested_candidate_source_root_is_rejected(tmp_path):
    base, _, _, _, output = _paths(tmp_path)
    merged = base / "nested-candidate"
    merged.mkdir()

    with pytest.raises(ValueError, match="canonically separated"):
        _canonicalize(base, merged, output)


def test_symlinked_model_source_root_is_rejected(tmp_path):
    base, _, _, _, output = _paths(tmp_path)
    alias = tmp_path / "candidate-alias"
    try:
        alias.symlink_to(base, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks are unavailable on this OS")

    with pytest.raises(ValueError, match="real non-reparse directory"):
        _canonicalize(base, alias, output)


def test_reparse_point_model_source_is_rejected_before_resolution(tmp_path, monkeypatch):
    base, merged, _, _, output = _paths(tmp_path)
    original_lstat = Path.lstat

    def lstat(path):
        if path == base:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_file_attributes=0x400,
            )
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="real non-reparse directory"):
        _canonicalize(base, merged, output)


def test_reparse_point_output_parent_is_rejected(tmp_path, monkeypatch):
    base, merged, _, _, _ = _paths(tmp_path)
    parent = tmp_path / "junction"
    parent.mkdir()
    output = parent / "export"
    original_lstat = Path.lstat

    def lstat(path):
        if path == parent:
            return SimpleNamespace(
                st_mode=stat.S_IFDIR | 0o755,
                st_file_attributes=0x400,
            )
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", lstat)
    with pytest.raises(ValueError, match="real non-reparse directory"):
        module._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=None,
        )
    assert not output.exists()


def test_current_model_cannot_be_inside_either_model_source_tree(tmp_path):
    base, merged, _, _, output = _paths(tmp_path)
    current = merged / "current.gguf"
    current.write_bytes(b"synthetic current model marker")

    with pytest.raises(ValueError, match="aliases a protected model source tree"):
        module._validate_export_output_path(
            output,
            base_dir=base,
            merged_candidate_dir=merged,
            current_model_path=current,
        )


def test_current_model_symlink_is_rejected(tmp_path):
    base, merged, _, _, output = _paths(tmp_path)
    current = tmp_path / "current.gguf"
    current.write_bytes(b"synthetic current model marker")
    alias = tmp_path / "current-alias.gguf"
    try:
        alias.symlink_to(current)
    except (OSError, NotImplementedError):
        pytest.skip("file symlinks are unavailable on this OS")

    with pytest.raises(ValueError, match="regular non-reparse file"):
        _canonicalize(base, merged, output, current=alias)


def test_current_model_must_exist_when_building_an_export_plan(tmp_path):
    base, merged, converter, quantizer, output = _paths(tmp_path)

    with pytest.raises(ValueError, match="existing regular file"):
        module._canonicalize_export_paths(
            base_dir=base,
            merged_candidate_dir=merged,
            output_dir=output,
            converter_path=converter,
            quantizer_path=quantizer,
            current_model_path=tmp_path / "missing-current.gguf",
            require_existing_model=True,
        )


def test_converter_and_quantizer_must_be_distinct_canonical_files(tmp_path):
    base, merged, converter, _, output = _paths(tmp_path)

    with pytest.raises(ValueError, match="distinct canonical files"):
        _canonicalize(
            base, merged, output,
            converter=converter,
            quantizer=converter,
        )


def test_converter_cannot_be_reused_as_a_model_source_file(tmp_path):
    base, merged, _, quantizer, output = _paths(tmp_path)
    converter = base / "convert.py"
    converter.write_text("# synthetic converter", encoding="utf-8")

    with pytest.raises(ValueError, match="separate from model source trees"):
        _canonicalize(
            base, merged, output,
            converter=converter,
            quantizer=quantizer,
        )


def test_build_export_plan_uses_absolute_canonical_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    base = Path("base-model")
    merged = Path("merged-candidate")
    base.mkdir()
    merged.mkdir()
    converter = Path("convert.py")
    quantizer = Path("quantize")
    converter.write_text("# converter", encoding="utf-8")
    quantizer.write_bytes(b"quantizer")
    output = Path("export")

    monkeypatch.setattr(module, "validate_experiment_001", lambda *_args, **_kwargs: "a" * 64)

    def tool_identity(path, *, git_revision, role):
        assert path.is_absolute()
        assert git_revision == "1" * 40
        return {
            "identity_sha256": (
                "b" * 64 if role == "hf_to_gguf_converter" else "c" * 64
            )
        }

    monkeypatch.setattr(module, "build_tool_identity", tool_identity)
    snapshot = {
        "export": {
            "llama_cpp_revision": "1" * 40,
            "converter_identity": "b" * 64,
            "quantizer_identity": "c" * 64,
        }
    }

    plan = module.build_export_plan(
        snapshot,
        base_dir=base,
        merged_candidate_dir=merged,
        converter_path=converter,
        quantizer_path=quantizer,
        output_dir=output,
    )

    assert plan.output_dir == str(output.absolute())
    assert plan.commands[0].argv[1] == str(converter.absolute())
    assert plan.commands[0].argv[2] == str(base.absolute())
    assert plan.commands[2].argv[1] == str(converter.absolute())
    assert plan.commands[2].argv[2] == str(merged.absolute())
    assert plan.commands[1].argv[0] == str(quantizer.absolute())
    assert not output.exists()
