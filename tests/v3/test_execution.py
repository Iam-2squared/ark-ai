import copy
import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked, load_snapshot, validate_experiment_001


TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def test_template_is_intentionally_blocked():
    with pytest.raises(ExecutionBlocked, match="unresolved execution identities"):
        validate_experiment_001(snapshot())


def test_contract_dataset_size_cannot_drift():
    value = snapshot()
    value["dataset"]["train_count"] = 50
    with pytest.raises(ExecutionBlocked, match="120 train / 30 validation"):
        validate_experiment_001(value)


def test_lora_precommit_cannot_drift():
    value = snapshot()
    value["method"]["rank"] = 16
    with pytest.raises(ExecutionBlocked, match="method.rank"):
        validate_experiment_001(value)


def test_v2_opening_budget_cannot_drift():
    value = snapshot()
    value["evaluation"]["v2_candidate_runs"] = 1
    with pytest.raises(ExecutionBlocked, match="2 Current . 2 Candidate"):
        validate_experiment_001(value)


def test_privacy_cannot_be_relaxed():
    value = snapshot()
    value["privacy"]["personal_memory_allowed"] = True
    with pytest.raises(ExecutionBlocked, match="privacy policy"):
        validate_experiment_001(value)


def test_snapshot_loader_requires_object(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_snapshot(path)


def test_authorization_is_separate_from_identity_closure():
    value = snapshot()

    def fill(obj):
        if isinstance(obj, dict):
            return {k: fill(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [fill(v) for v in obj]
        if obj == "UNRESOLVED" or (isinstance(obj, str) and obj.endswith("_REQUIRED")):
            return "frozen"
        if obj == "USER_APPROVAL_REQUIRED":
            return "approved-ceiling"
        return obj

    value = fill(copy.deepcopy(value))
    # SAME_AS_BASE and NOT_REQUIRED_UNLESS_APPROVED are intentional resolved policy values.
    digest = validate_experiment_001(value)
    assert len(digest) == 64
    with pytest.raises(ExecutionBlocked, match="explicit real-training"):
        validate_experiment_001(value, require_training_authorization=True)

    value["authorization"]["real_training_authorized"] = True
    value["authorization"]["external_compute_authorized"] = True
    digest = validate_experiment_001(value, require_training_authorization=True)
    assert len(digest) == 64


def test_v2_and_promotion_cannot_be_pre_authorized():
    value = snapshot()
    value["authorization"]["v2_opening_authorized"] = True
    with pytest.raises(ExecutionBlocked, match="may not pre-authorize"):
        validate_experiment_001(value)
