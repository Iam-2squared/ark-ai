"""Final proactive/readiness diagnostic must remain inert and untampered.

All scheduler, readiness and observation inputs are synthetic; the callback
used below mutates a frozen local receipt during its own constructor only.
No camera, notification, network or actual ToolBackend runs.
"""

from pathlib import Path

import pytest

import ark.proactive_startup_fence_review as module
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness


def _equal_distinct(text):
    replacement = ("!" + text)[1:]
    assert replacement == text and replacement is not text
    return replacement


def _case(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline-private", "notes", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-1"),
        StartupComponent(
            "scheduler", dependencies=("memory",),
            schema_revision="scheduler-1",
        ),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-1"),
        SyntheticReadinessRequirement("scheduler", "scheduler-1"),
    )
    return ledger, receipt, policy, snapshot, requirements


def _run(state):
    ledger, receipt, policy, snapshot, requirements = state
    return module.review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements,
        source_digest="a" * 64,
        observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100,
        max_startup_age_ms=5, max_observation_age_ms=10,
    )


@pytest.mark.parametrize("mutation", (
    "result_trigger",
    "result_readiness",
    "result_history",
    "result_time",
    "input_receipt",
    "input_policy",
    "input_source",
    "input_snapshot",
    "returned_trigger",
    "returned_readiness",
))
def test_proactive_constructor_callback_cannot_retarget_review(
    tmp_path, monkeypatch, mutation,
):
    state = _case(tmp_path)
    original_init = module.SyntheticProactiveStartupReview.__init__
    seen_trigger = []
    seen_ready = []
    native_trigger = module.review_prepared_trigger_freshness
    native_ready = module.review_synthetic_startup_lease

    def trigger(*args, **kwargs):
        result = native_trigger(*args, **kwargs)
        seen_trigger.append(result)
        return result

    def ready(*args, **kwargs):
        result = native_ready(*args, **kwargs)
        seen_ready.append(result)
        return result

    def injected_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if mutation == "result_trigger":
            object.__setattr__(self, "trigger_id", _equal_distinct(self.trigger_id))
        elif mutation == "result_readiness":
            object.__setattr__(
                self, "readiness_digest", _equal_distinct(self.readiness_digest),
            )
        elif mutation == "result_history":
            object.__setattr__(
                self, "trigger_history_digest",
                _equal_distinct(self.trigger_history_digest),
            )
        elif mutation == "result_time":
            object.__setattr__(self, "checked_at_ms", 101)
        elif mutation == "input_receipt":
            original = state[1].trigger_id
            object.__setattr__(state[1], "trigger_id", _equal_distinct(original))
        elif mutation == "input_policy":
            original = state[2].policy_revision
            object.__setattr__(state[2], "policy_revision", _equal_distinct(original))
        elif mutation == "input_source":
            state[0].path = Path(str(state[0].path))
        elif mutation == "input_snapshot":
            object.__setattr__(
                state[3].components[0], "schema_revision", "forged",
            )
        elif mutation == "returned_trigger":
            object.__setattr__(
                seen_trigger[0], "trigger_id",
                _equal_distinct(seen_trigger[0].trigger_id),
            )
        else:
            object.__setattr__(
                seen_ready[0], "snapshot_digest",
                _equal_distinct(seen_ready[0].snapshot_digest),
            )

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", trigger)
    monkeypatch.setattr(module, "review_synthetic_startup_lease", ready)
    monkeypatch.setattr(module.SyntheticProactiveStartupReview, "__init__", injected_init)
    with pytest.raises(
        module.SyntheticProactiveStartupRejected,
        match="constructed|input|source|snapshot",
    ):
        _run(state)
    assert len(seen_trigger) == 2
    assert len(seen_ready) == 2


def test_stable_proactive_result_still_denies_all_external_effects(tmp_path):
    result = _run(_case(tmp_path))
    assert result.trigger_id.startswith("trigger_")
    assert result.trigger_history_digest.startswith("synthetic_triggers_")
    assert result.checked_at_ms == 100
    assert not result.startup_authorized
    assert not result.notification_authorized
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
