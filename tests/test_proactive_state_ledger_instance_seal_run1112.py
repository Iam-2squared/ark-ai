"""Run1112: proactive state ledger path identity is immutable per instance."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateLedger,
    SyntheticProactiveStateRejected,
)


def _policy() -> SyntheticProactivePolicy:
    return SyntheticProactivePolicy(
        owner="owner-a",
        namespace="personal",
        definition_id="daily-summary",
        revision=1,
        policy_revision="policy-v1",
        minimum_interval_ms=100,
        cooldown_ms=200,
        rolling_window_ms=1000,
        max_previews_per_window=2,
    )


def test_ledger_has_no_instance_dictionary_or_mutable_path(tmp_path: Path) -> None:
    path = tmp_path / "proactive.sqlite"
    replacement = tmp_path / "replacement.sqlite"
    ledger = SyntheticProactiveStateLedger(path)

    assert not hasattr(ledger, "__dict__")
    assert ledger.path is path

    with pytest.raises(AttributeError, match="identity is immutable"):
        ledger.path = replacement
    with pytest.raises(AttributeError, match="identity is immutable"):
        ledger._path = replacement
    with pytest.raises(AttributeError, match="identity is immutable"):
        del ledger._path
    with pytest.raises(AttributeError, match="identity is immutable"):
        ledger.extra = "redirect"

    assert ledger.path is path
    assert ledger.read_state(_policy()) is None
    assert not replacement.exists()


def test_ledger_rejects_subclass_before_creating_a_database(tmp_path: Path) -> None:
    class DerivedLedger(SyntheticProactiveStateLedger):
        pass

    path = tmp_path / "subclass.sqlite"

    with pytest.raises(SyntheticProactiveStateRejected, match="exact proactive state ledger"):
        DerivedLedger(path)

    assert not path.exists()
