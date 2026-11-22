"""Run1121: proactive ledger class descriptors are pinned before SQLite I/O."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.proactive_state_ledger as ledger_module
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


@pytest.mark.parametrize(
    "member",
    ("_connect", "evaluate", "count", "path", "__setattr__", "__delattr__"),
)
def test_class_descriptor_replacement_is_rejected_before_database_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    member: str,
) -> None:
    path = tmp_path / "must-not-be-created.sqlite"
    invoked: list[str] = []

    def replacement(*_args: object, **_kwargs: object) -> object:
        invoked.append(member)
        raise AssertionError("substituted ledger descriptor must not execute")

    monkeypatch.setattr(SyntheticProactiveStateLedger, member, replacement)

    with pytest.raises(
        SyntheticProactiveStateRejected,
        match="class descriptor changed",
    ):
        SyntheticProactiveStateLedger(path)

    assert invoked == []
    assert not path.exists()


def test_rebound_ledger_method_vector_is_rejected_before_read(tmp_path: Path, monkeypatch):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    monkeypatch.setattr(ledger_module, "_LEDGER_METHODS", ())

    with pytest.raises(
        SyntheticProactiveStateRejected,
        match="class descriptor changed",
    ):
        ledger.read_state(_policy())
