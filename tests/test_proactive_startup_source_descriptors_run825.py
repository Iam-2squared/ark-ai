"""Source descriptor custody for disconnected proactive startup reviews.

A substituted class-level getter on a locally retained receipt must be
rejected before dual source reads. No live notifications or trusted clocks.
"""

from __future__ import annotations

import pytest

import ark.proactive_startup_fence_review as proactive


@pytest.mark.parametrize(
    ("carrier", "field"),
    (
        ("SyntheticTriggerReceipt", "trigger_id"),
        ("SyntheticTriggerPolicy", "owner"),
        ("SyntheticTriggerPolicy", "policy_revision"),
        ("SyntheticTriggerWitness", "row_hashes"),
        ("StartupSnapshot", "components"),
        ("StartupSnapshot", "digest"),
        ("ComponentResult", "effective_state"),
        ("SyntheticReadinessRequirement", "component_id"),
    ),
)
def test_proactive_source_descriptor_substitution_denied_without_callback(
    monkeypatch, carrier: str, field: str,
) -> None:
    touched = []

    def hostile_getter(_):
        touched.append((carrier, field))
        raise AssertionError("untrusted private receipt property executed")

    cls = getattr(proactive, carrier)
    with monkeypatch.context() as patch:
        patch.setattr(cls, field, property(hostile_getter))
        with pytest.raises(
            proactive.SyntheticProactiveStartupRejected,
            match="descriptor epoch changed",
        ):
            proactive._require_original_authorities()
    assert touched == []


@pytest.mark.parametrize(
    "carrier", ("SyntheticTriggerPolicy", "StartupSnapshot"),
)
def test_proactive_source_class_identity_replacement_denied(
    monkeypatch, carrier: str,
) -> None:
    class FalseReceipt:
        def __getattribute__(self, _name):
            raise AssertionError("forged readiness carrier executed")

    with monkeypatch.context() as patch:
        patch.setattr(proactive, carrier, FalseReceipt)
        with pytest.raises(
            proactive.SyntheticProactiveStartupRejected,
            match="descriptor epoch changed",
        ):
            proactive._require_original_authorities()


def test_unmodified_proactive_source_contract_stays_unchanged() -> None:
    assert proactive._require_original_authorities() is None
