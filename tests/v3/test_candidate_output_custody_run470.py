"""Validation-only Candidate output path custody; no GPU/model execution."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning import hf_lora as module
from ark.learning.hf_lora import (
    HfLoRAFullRun,
    LoRARuntimeError,
    _validate_candidate_output_path,
)


def test_new_sibling_output_passes_path_precheck_without_creating_it(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    output = tmp_path / "candidate"
    _validate_candidate_output_path(output, base)
    assert not output.exists()


@pytest.mark.parametrize("kind", ["existing", "missing-parent", "traversal", "inside-base"])
def test_candidate_output_rejects_unsafe_or_input_overlapping_paths(tmp_path, kind):
    base = tmp_path / "base"
    base.mkdir()
    inner = base / "artifacts"
    inner.mkdir()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    existing = tmp_path / "existing"
    existing.mkdir()
    paths = {
        "existing": existing,
        "missing-parent": tmp_path / "not-created" / "candidate",
        "traversal": scratch / ".." / "candidate",
        "inside-base": inner / "candidate",
    }
    with pytest.raises(LoRARuntimeError, match="Candidate output"):
        _validate_candidate_output_path(paths[kind], base)


def test_candidate_output_rejects_symlinked_parent_when_supported(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    destination = tmp_path / "destination"
    destination.mkdir()
    link = tmp_path / "shortcut"
    try:
        link.symlink_to(destination, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("test environment disallows synthetic directory symlinks")
    with pytest.raises(LoRARuntimeError, match="Candidate output"):
        _validate_candidate_output_path(link / "candidate", base)


def test_full_run_rejects_overlapping_output_before_local_identity_or_gpu(
    tmp_path, monkeypatch,
):
    base = tmp_path / "base"
    base.mkdir()
    output = base / "candidate"
    runner = HfLoRAFullRun(
        base_dir=base,
        dataset_path=tmp_path / "dataset",
        chat_template_probe=tmp_path / "probe",
        output_dir=output,
    )
    monkeypatch.setattr(
        module, "validate_experiment_001",
        lambda snapshot, authorization_scope: "a" * 64,
    )

    def must_not_reach(*args, **kwargs):
        raise AssertionError("unsafe output must be rejected before model access")

    monkeypatch.setattr(module, "_verify_local_identities", must_not_reach)
    monkeypatch.setattr(module, "_build_model_and_tokenizer", must_not_reach)
    with pytest.raises(LoRARuntimeError, match="inside base model"):
        runner.run({"budget": {"wall_clock_timeout_minutes": 60}})
    assert not output.exists()


def test_path_validation_does_not_mutate_external_inputs(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    output = Path(tmp_path) / "candidate"
    _validate_candidate_output_path(output, base)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["base"]
