"""Cross-review custody of original startup components and retained history.

All probes and triggers are disconnected fixtures. No real notification, tool
dispatch, sensor read, authenticated timestamp or user authorization is used.
"""

import pytest

import ark.proactive_startup_fence_review as fence
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy
from ark.startup_readiness_lease_review import SyntheticReadinessRequirement
from ark.startup_readiness_review import StartupComponent, evaluate_startup_readiness


def _clone(value):
    replacement = ("!" + value)[1:]
    assert replacement == value and replacement is not value
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
    retained = read_proactive_witness(ledger)
    return ledger, receipt, policy, snapshot, requirements, retained


def _review(case):
    ledger, receipt, policy, snapshot, requirements, retained = case
    return fence.review_synthetic_proactive_startup(
        ledger, receipt, policy, snapshot, requirements,
        source_digest="a" * 64, observation_digest="b" * 64,
        captured_at_ms=98, now_ms=100, max_startup_age_ms=5,
        max_observation_age_ms=10, retained=retained,
    )


@pytest.mark.parametrize("mutation", (
    "component_id", "schema_revision", "component_dependencies",
    "component_tuple", "snapshot_digest", "retained_digest", "retained_rows",
))
def test_trigger_review_cannot_replace_equal_startup_or_retained_carrier(
    tmp_path, monkeypatch, mutation,
):
    case = _case(tmp_path)
    snapshot, retained = case[3], case[5]
    native = fence.review_prepared_trigger_freshness
    called = []

    def mutate_after_first_trigger(*args, **kwargs):
        result = native(*args, **kwargs)
        if not called:
            if mutation in {"component_id", "schema_revision"}:
                item = snapshot.components[0]
                object.__setattr__(
                    item, mutation, _clone(getattr(item, mutation)),
                )
            elif mutation == "component_dependencies":
                item = snapshot.components[1]
                deps = tuple(list(item.dependencies))
                assert deps == item.dependencies and deps is not item.dependencies
                object.__setattr__(item, "dependencies", deps)
            elif mutation == "component_tuple":
                components = tuple(list(snapshot.components))
                assert components == snapshot.components
                assert components is not snapshot.components
                object.__setattr__(snapshot, "components", components)
            elif mutation == "snapshot_digest":
                object.__setattr__(
                    snapshot, "digest", _clone(snapshot.digest),
                )
            elif mutation == "retained_digest":
                object.__setattr__(retained, "digest", _clone(retained.digest))
            else:
                hashes = tuple(list(retained.row_hashes))
                assert hashes == retained.row_hashes
                assert hashes is not retained.row_hashes
                object.__setattr__(retained, "row_hashes", hashes)
        called.append(True)
        return result

    monkeypatch.setattr(
        fence, "review_prepared_trigger_freshness", mutate_after_first_trigger,
    )
    with pytest.raises(
        fence.SyntheticProactiveStartupRejected,
        match="startup trigger input, source or retained evidence changed",
    ):
        _review(case)
    assert called == [True]


def test_unchanged_startup_and_retained_evidence_remain_deny_only(tmp_path):
    result = _review(_case(tmp_path))
    assert result.trigger_id.startswith("trigger_")
    assert result.readiness_digest
    assert result.trigger_history_digest.startswith("synthetic_triggers_")
    assert result.checked_at_ms == 100
    assert not result.startup_authorized
    assert not result.notification_authorized
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
