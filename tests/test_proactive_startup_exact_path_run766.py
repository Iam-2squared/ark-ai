"""Proactive startup cannot inspect private fixtures through dynamic Paths.

Only inert read-only synthetic gates are exercised. No notification, model,
device, network or ToolBackend is invoked by these malformed-input tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.proactive_startup_fence_review import (
    SyntheticProactiveStartupRejected,
    review_synthetic_proactive_startup,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
)
from ark.startup_readiness_review import StartupSnapshot


class TrappedPath(type(Path("."))):
    @property
    def parents(self):
        raise AssertionError("untrusted startup path ancestors read")

    def resolve(self, *args, **kwargs):
        raise AssertionError("untrusted startup path resolution executed")


@pytest.mark.parametrize("dynamic_source", ("subclass", "string", "null"))
def test_proactive_source_type_denied_before_any_private_receipt_field(
    tmp_path: Path,
    dynamic_source: str,
) -> None:
    # Build uninitialized exact typed carriers: the source check must reject
    # before even trying to inspect the receipt/policy/snapshot attributes.
    ledger = object.__new__(SyntheticProactiveLedger)
    if dynamic_source == "subclass":
        ledger.path = TrappedPath(str(tmp_path / "trigger.sqlite"))
    elif dynamic_source == "string":
        ledger.path = str(tmp_path / "trigger.sqlite")
    else:
        ledger.path = None
    receipt = object.__new__(SyntheticTriggerReceipt)
    policy = object.__new__(SyntheticTriggerPolicy)
    snapshot = object.__new__(StartupSnapshot)
    with pytest.raises(
        SyntheticProactiveStartupRejected,
        match="exact local startup trigger source required",
    ):
        review_synthetic_proactive_startup(
            ledger, receipt, policy, snapshot, (),
            source_digest="a" * 64,
            observation_digest="b" * 64,
            captured_at_ms=1,
            now_ms=2,
            max_startup_age_ms=10,
            max_observation_age_ms=10,
        )
    assert not (tmp_path / "trigger.sqlite").exists()
