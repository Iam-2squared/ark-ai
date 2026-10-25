"""Offline freshness diagnostics bind constructed history and result carriers.

All triggered faults are synthetic. No notification, hardware action, consent,
clock attestation or tool dispatch can be inferred from a passing fixture.
"""

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_continuity_review import (
    SyntheticTriggerWitness,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "freshness.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "fixture", "reminder", 1, "policy-v1", 5, 50, 3
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _review(state, **kwargs):
    ledger, policy, receipt = state
    return module.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10, **kwargs,
    )


def _same_value_new_string(value):
    swapped = ("!" + value)[1:]
    assert swapped == value and swapped is not value
    return swapped


@pytest.mark.parametrize("field", ("row_hashes", "digest"))
def test_continuity_callback_cannot_swap_constructed_history_carriers(
    tmp_path, monkeypatch, field,
):
    state = _fixture(tmp_path)
    retained = read_proactive_witness(state[0])
    original = module.assert_proactive_history_continues

    def drift_after_check(previous, current):
        original(previous, current)
        if field == "row_hashes":
            original_rows = current.row_hashes
            replacement = tuple(list(original_rows))
            assert replacement == original_rows
            assert replacement is not original_rows
            object.__setattr__(current, "row_hashes", replacement)
        else:
            object.__setattr__(
                current, "digest", _same_value_new_string(current.digest)
            )

    monkeypatch.setattr(
        module, "assert_proactive_history_continues", drift_after_check
    )
    with pytest.raises(SyntheticTriggerRejected, match="freshness history changed"):
        _review(state, retained=retained)


@pytest.mark.parametrize(
    "target",
    (
        "trigger_id", "prepared_at_ms", "checked_at_ms",
        "history", "history_rows", "history_digest",
    ),
)
def test_final_result_constructor_cannot_return_a_different_epoch(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    review_type = module.SyntheticProactiveFreshnessReview
    original_init = review_type.__init__

    def changed_init(self, *args):
        original_init(self, *args)
        if target == "trigger_id":
            object.__setattr__(
                self, "trigger_id", _same_value_new_string(self.trigger_id)
            )
        elif target == "prepared_at_ms":
            object.__setattr__(self, "prepared_at_ms", 101)
        elif target == "checked_at_ms":
            object.__setattr__(self, "checked_at_ms", 101)
        elif target == "history":
            historical = self.history
            object.__setattr__(
                self, "history",
                SyntheticTriggerWitness(
                    historical.row_hashes, historical.digest
                ),
            )
        elif target == "history_rows":
            original_rows = self.history.row_hashes
            object.__setattr__(
                self.history, "row_hashes", tuple(list(original_rows))
            )
        else:
            object.__setattr__(
                self.history, "digest",
                _same_value_new_string(self.history.digest),
            )

    monkeypatch.setattr(review_type, "__init__", changed_init)
    with pytest.raises(
        SyntheticTriggerRejected, match="freshness (history|review output) changed"
    ):
        _review(state)


def test_untampered_freshness_remains_deterministic_and_non_authorizing(tmp_path):
    state = _fixture(tmp_path)
    retained = read_proactive_witness(state[0])
    first = _review(state, retained=retained)
    second = _review(state, retained=retained)
    assert first == second
    assert first.trigger_id is state[2].trigger_id or (
        first.trigger_id == state[2].trigger_id
    )
    assert first.history == retained
    assert first.notification_authorized is False
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
