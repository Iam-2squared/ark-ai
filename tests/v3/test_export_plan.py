import json
from pathlib import Path

import pytest

from ark.learning.export_plan import build_export_plan
from ark.learning.identity import build_tool_identity


TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def resolved_snapshot(converter, quantizer):
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    revision = "3" * 40
    value["code"]["git_sha"] = "1" * 40
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
        {"device": "gpu", "vram_gib": 24, "driver": "driver", "preflight_report_sha256": "UNRESOLVED"}
    )
    value["budget"].update({"max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60})
    value["export"].update(
        {
            "llama_cpp_revision": revision,
            "converter_identity": build_tool_identity(
                converter, git_revision=revision, role="hf_to_gguf_converter"
            )["identity_sha256"],
            "quantizer_identity": build_tool_identity(
                quantizer, git_revision=revision, role="quantizer"
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
    converter.write_bytes(b"changed")
    with pytest.raises(ValueError, match="converter bytes"):
        build_export_plan(
            snapshot,
            base_dir=tmp_path,
            merged_candidate_dir=tmp_path,
            converter_path=converter,
            quantizer_path=quantizer,
            output_dir=tmp_path / "out",
        )
