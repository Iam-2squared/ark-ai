"""Passive V3 identity shapes reject invisible/control-bearing labels.

A syntactically clean report is never evidence of model bytes, authorization,
provider billing caps, human approval, Candidate readiness or V2 opening.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning.offline_snapshot_shape_review import (
    review_unapproved_v3_snapshot_shapes,
)

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


@pytest.mark.parametrize(
    "path,value",
    (
        ("environment.python", "3.12\nunsafe"),
        ("environment.cuda_runtime", "12.4\x00extra"),
        ("environment.os_or_image_digest", " Ubuntu-22.04"),
        ("hardware.driver", "535.104\r"),
        ("hardware.device", "GPU\x7fhidden"),
        ("export.llama_cpp_revision", "c" * 39 + "\x00"),
        ("environment.torch", "2.5\u200b.1"),
    ),
)
def test_invisible_and_padded_pins_remain_invalid_without_authorization(
    path, value,
):
    snapshot = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    section, field = path.split(".")
    snapshot[section][field] = value
    report = review_unapproved_v3_snapshot_shapes(snapshot)
    assert path in report.invalid_shape_paths
    assert path not in report.unresolved_paths
    assert report.external_compute_authorized is False
    assert report.preflight_authorized is False
    assert report.real_training_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.v2_opening_authorized is False
    assert report.promotion_authorized is False


@pytest.mark.parametrize(
    "path,value",
    (
        ("environment.python", "3.12.10"),
        ("hardware.driver", "535.104"),
        ("hardware.device", "NVIDIA RTX 4090"),
        ("environment.os_or_image_digest", "linux:sha256:synthetic"),
    ),
)
def test_readable_synthetic_labels_remain_only_shape_hints(path, value):
    snapshot = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    section, field = path.split(".")
    snapshot[section][field] = value
    report = review_unapproved_v3_snapshot_shapes(snapshot)
    assert path not in report.invalid_shape_paths
    assert path not in report.unresolved_paths
    assert report.real_training_authorized is False
