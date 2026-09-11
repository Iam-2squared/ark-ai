import copy
import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked, load_snapshot, validate_experiment_001

TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def resolved_snapshot():
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    value["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    value["base"].update({"revision": "2" * 40, "file_sha256_manifest": "a" * 64})
    value["tokenizer"].update(
        {
            "file_sha256_manifest": "b" * 64,
            "chat_template_probe_sha256": "c" * 64,
        }
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
            "os_or_image_digest": "linux-image@sha256:abc",
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
            "device": "approved-gpu",
            "vram_gib": 24,
            "driver": "pinned-driver",
            "preflight_report_sha256": "UNRESOLVED",
        }
    )
    value["budget"].update({"max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60})
    value["export"].update(
        {
            "llama_cpp_revision": "3" * 40,
            "converter_identity": "4" * 64,
            "quantizer_identity": "5" * 64,
        }
    )
    return value


@pytest.mark.parametrize(
    ("section", "field", "bad"),
    [
        ("hardware", "vram_gib", float("nan")),
        ("hardware", "vram_gib", float("inf")),
        ("budget", "max_cost_jpy", float("nan")),
        ("budget", "max_cost_jpy", float("inf")),
        ("budget", "wall_clock_timeout_minutes", float("nan")),
        ("budget", "wall_clock_timeout_minutes", float("inf")),
    ],
)
def test_non_finite_runtime_and_budget_numbers_are_rejected(section, field, bad):
    value = copy.deepcopy(resolved_snapshot())
    value[section][field] = bad
    with pytest.raises(ExecutionBlocked, match="finite positive numeric value required"):
        validate_experiment_001(value)


def test_nonstandard_json_constants_are_rejected_at_load_boundary(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text('{"x":NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        load_snapshot(path)
