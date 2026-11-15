"""Planner retained replay tails enforce exact widths before digest regexes.

All evidence is synthetic, disconnected and deny-only. These tests do not
grant dispatch or automatic replay of a RUNNING/UNKNOWN step.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency import planner_journal_review as journal


def _tail() -> journal.SyntheticPlanTail:
    return journal.SyntheticPlanTail(
        topology_digest="plan_" + "a" * 64,
        event_count=0,
        event_hash="pevt_" + "b" * 64,
        status_digest="pstate_" + "c" * 64,
        last_at_ms=-1,
    )


class _ExplodingPattern:
    def fullmatch(self, _value: object) -> None:
        raise AssertionError("oversized retained digest reached regex")


@pytest.mark.parametrize(
    ("field", "pattern"),
    (
        ("topology_digest", "_PLAN"),
        ("event_hash", "_HEX"),
        ("status_digest", "_STATE"),
    ),
)
def test_oversized_retained_digest_denied_before_regex(
    monkeypatch: pytest.MonkeyPatch, field: str, pattern: str,
) -> None:
    malformed = replace(_tail(), **{field: "a" * 100_000})
    monkeypatch.setattr(journal, pattern, _ExplodingPattern())
    with pytest.raises(
        journal.SyntheticPlanJournalRejected, match="retained synthetic plan tail",
    ):
        malformed.assert_shape()


@pytest.mark.parametrize(
    ("field", "malformed"),
    (
        ("topology_digest", "plan_" + "g" * 64),
        ("event_hash", "pevt_" + "g" * 64),
        ("status_digest", "pstate_" + "g" * 64),
    ),
)
def test_correct_width_with_invalid_hex_is_still_rejected(
    field: str, malformed: str,
) -> None:
    with pytest.raises(
        journal.SyntheticPlanJournalRejected, match="retained synthetic plan tail",
    ):
        replace(_tail(), **{field: malformed}).assert_shape()


def test_valid_genesis_shape_and_inert_recovery() -> None:
    tail = _tail()
    tail.assert_shape()
    recovered = journal.SyntheticPlanRecovery(
        tail, (("local_step", "RUNNING", 1),), ("local_step",),
    )
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
