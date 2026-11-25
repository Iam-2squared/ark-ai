"""Run1203: V3 dataset JSON inputs reject duplicate object members."""

import pytest

from ark.learning.dataset import DatasetArtifact, digest, loads_unique_json
from ark.learning.dataset_cli import _accepted, _load_json_list
from ark.learning.freeze import _accepted_items
from ark.learning.training import MockTrainingBackend, TrainingConfig


def test_duplicate_keys_are_rejected_at_every_object_depth() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        loads_unique_json('{"outer":{"candidate_id":"first","candidate_id":"second"}}')


def test_same_key_in_separate_objects_is_not_a_duplicate() -> None:
    assert loads_unique_json('{"left":{"value":1},"right":{"value":2}}') == {
        "left": {"value": 1},
        "right": {"value": 2},
    }


def test_dataset_cli_rejects_duplicate_candidate_fields(tmp_path) -> None:
    path = tmp_path / "candidates.json"
    path.write_text(
        '[{"candidate_id":"reviewed-id","candidate_id":"shadow-id"}]',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate JSON key"):
        _load_json_list(path, "candidates")


def test_dataset_payload_consumers_reject_duplicate_nested_candidate_fields(
    tmp_path,
) -> None:
    payload = (
        b'{"schema_version":1,"examples":['
        b'{"candidate_id":"reviewed-id","candidate_id":"shadow-id"}]}'
    )
    artifact = DatasetArtifact(payload, digest(payload), {})
    config = TrainingConfig(
        "mock-only",
        "b" * 64,
        artifact.sha256,
        "c" * 40,
        "synthetic dependencies",
        "synthetic CPU",
    )

    with pytest.raises(ValueError, match="duplicate JSON key"):
        _accepted(payload)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        _accepted_items(artifact)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        MockTrainingBackend().train(artifact, config, tmp_path / "run")

    assert not (tmp_path / "run").exists()
