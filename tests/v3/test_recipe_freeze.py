import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked, validate_experiment_001


TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def test_adamw_mathematical_defaults_are_explicitly_frozen():
    method = snapshot()["method"]
    assert method["optimizer"] == "adamw_torch"
    assert method["optimizer_betas"] == [0.9, 0.999]
    assert method["optimizer_eps"] == 1e-8
    assert method["optimizer_weight_decay"] == 0.01
    assert method["optimizer_amsgrad"] is False
    assert method["optimizer_maximize"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("optimizer_betas", [0.8, 0.999]),
        ("optimizer_eps", 1e-7),
        ("optimizer_weight_decay", 0.0),
        ("optimizer_amsgrad", True),
        ("optimizer_maximize", True),
    ],
)
def test_optimizer_recipe_drift_is_blocked_before_identity_resolution(field, value):
    value_snapshot = snapshot()
    value_snapshot["method"][field] = value
    with pytest.raises(ExecutionBlocked, match=f"method.{field}"):
        validate_experiment_001(value_snapshot)
