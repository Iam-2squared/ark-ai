import json
from pathlib import Path

import pytest

import ark.learning.export_plan as export_plan
from ark.learning.export_plan import build_export_plan
from ark.learning.identity import build_tool_identity

TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def resolved_snapshot(converter, quantizer):
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    revision = "3" * 40
    value["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    value["base"].update({"revision": "2" * 40, "file_sha256_manifest": "a" * 64})
    value["tokenizer"].update(
        {"file_sha256_manifest": "b" * 64, "chat_template_probe_sha256": "c" * 64}
    )
    value["dataset"].update(
        {
            "canonical_sha256": "d" * 64,
            "provenance_manifest_sha256": "e" * 64,
            "contamination_report_sha256": "f" * 64,
        }
    )
    value["environment"].update(
        {
            "os_or_image_digest": "image@sha256:abc",
            "python": "3.12.10",
            "torch": "pinned",
            "transformers": "pinned",
            "peft": "pinned",
            "accelerate": "pinned",
            "cuda_runtime": "pinned",
        }
    )
    value["hardware"].update(
        {
            "device": "gpu",
            "vram_gib": 24,
            "driver": "driver",
            "preflight_report_sha256": "UNRESOLVED",
        }
    )
    value["budget"].update({"max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60})
    value["export"].update(
        {
            "llama_cpp_revision": revision,
            "converter_identity": build_tool_identity(
                converter,
                git_revision=revision,
                role="hf_to_gguf_converter",
            )["identity_sha256"],
            "quantizer_identity": build_tool_identity(
                quantizer,
                git_revision=revision,
                role="quantizer",
            )["identity_sha256"],
        }
    )
    return value


def test_export_plan_is_paired_and_non_executing(tmp_path):
    converter = tmp_path / "convert_hf_to_gguf.py"
    quantizer = tmp_path / "llama-quantize"
    converter.write_text("# converter", encoding="utf-8")
    quantizer.write_bytes(b"quantizer")
    base = tmp_path / "base"
    merged = tmp_path / "merged"
    base.mkdir()
    merged.mkdir()
    output = tmp_path / "export"

    plan = build_export_plan(
        resolved_snapshot(converter, quantizer),
        base_dir=base,
        merged_candidate_dir=merged,
        converter_path=converter,
        quantizer_path=quantizer,
        output_dir=output,
    )
    assert not output.exists()
    assert plan.quantization == "Q4_K_M"
    assert len(plan.commands) == 4
    assert plan.commands[0].role == "paired_current_convert"
    assert plan.commands[2].role == "candidate_convert"
    assert plan.candidate_q4km.endswith("candidate-Q4_K_M.gguf")
    assert plan.paired_current_q4km.endswith("paired-current-Q4_K_M.gguf")
    assert len(plan.sha256) == 64


def test_export_plan_rejects_unpinned_converter_bytes(tmp_path):
    converter = tmp_path / "convert.py"
    quantizer = tmp_path / "quantize"
    converter.write_bytes(b"one")
    quantizer.write_bytes(b"two")
    snapshot = resolved_snapshot(converter, quantizer)
    # Keep distinct existing input roots so the byte-identity regression
    # exercises converter drift rather than the independent output-overlap gate.
    base = tmp_path / "base"
    merged = tmp_path / "merged"
    base.mkdir()
    merged.mkdir()
    converter.write_bytes(b"changed")
    with pytest.raises(ValueError, match="converter bytes"):
        build_export_plan(
            snapshot,
            base_dir=base,
            merged_candidate_dir=merged,
            converter_path=converter,
            quantizer_path=quantizer,
            output_dir=tmp_path / "out",
        )


@pytest.mark.parametrize(
    "executable",
    ("", "   ", "py\x00thon", "x" * 4097, "\ud800"),
    ids=("empty", "blank", "nul", "codepoint-budget", "invalid-utf8"),
)
def test_invalid_python_executable_is_rejected_before_snapshot_or_file_access(
    tmp_path, monkeypatch, executable,
):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("snapshot or tool identity was accessed before argv admission")

    monkeypatch.setattr(export_plan, "validate_experiment_001", unexpected)
    monkeypatch.setattr(export_plan, "build_tool_identity", unexpected)
    with pytest.raises(ValueError, match="python executable"):
        build_export_plan(
            {},
            base_dir=tmp_path / "base",
            merged_candidate_dir=tmp_path / "merged",
            converter_path=tmp_path / "converter",
            quantizer_path=tmp_path / "quantizer",
            output_dir=tmp_path / "out",
            python_executable=executable,
        )


def test_python_executable_subclass_is_rejected_before_string_callbacks(
    tmp_path, monkeypatch,
):
    class HostileExecutable(str):
        def __len__(self):
            raise AssertionError("length callback ran")

        def strip(self):
            raise AssertionError("strip callback ran")

        def encode(self, *_args, **_kwargs):
            raise AssertionError("encoding callback ran")

    monkeypatch.setattr(
        export_plan,
        "validate_experiment_001",
        lambda *_args, **_kwargs: pytest.fail("snapshot validation ran"),
    )
    with pytest.raises(ValueError, match="python executable"):
        build_export_plan(
            {},
            base_dir=tmp_path / "base",
            merged_candidate_dir=tmp_path / "merged",
            converter_path=tmp_path / "converter",
            quantizer_path=tmp_path / "quantizer",
            output_dir=tmp_path / "out",
            python_executable=HostileExecutable("python"),
        )


def test_python_executable_budget_cannot_be_rebound(tmp_path, monkeypatch):
    monkeypatch.setattr(export_plan, "_MAX_PYTHON_EXECUTABLE_BYTES", 4097)
    with pytest.raises(ValueError, match="python executable byte budget changed"):
        build_export_plan(
            {},
            base_dir=tmp_path / "base",
            merged_candidate_dir=tmp_path / "merged",
            converter_path=tmp_path / "converter",
            quantizer_path=tmp_path / "quantizer",
            output_dir=tmp_path / "out",
        )


def test_valid_python_executable_is_preserved_as_one_argv_item(tmp_path):
    converter = tmp_path / "convert.py"
    quantizer = tmp_path / "quantize"
    converter.write_bytes(b"converter")
    quantizer.write_bytes(b"quantizer")
    base = tmp_path / "base"
    merged = tmp_path / "merged"
    base.mkdir()
    merged.mkdir()
    output = tmp_path / "export"
    executable = r"C:\Program Files\Python\python.exe"

    plan = build_export_plan(
        resolved_snapshot(converter, quantizer),
        base_dir=base,
        merged_candidate_dir=merged,
        converter_path=converter,
        quantizer_path=quantizer,
        output_dir=output,
        python_executable=executable,
    )

    assert plan.commands[0].argv[0] is executable
    assert plan.commands[2].argv[0] is executable
    assert not output.exists()
