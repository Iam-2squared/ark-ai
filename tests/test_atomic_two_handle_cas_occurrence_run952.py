"""Run952: stale independently opened atomic intent writers cannot reserve twice.

Synthetic SQLite only. A committed local intent/audit pair does not authorize
tool dispatch, authenticate approval, or prove an external effect.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )


def _rows(path) -> tuple[object, object]:
    with sqlite3.connect(path) as conn:
        return (
            conn.execute("SELECT * FROM intents ORDER BY seq").fetchall(),
            conn.execute("SELECT * FROM preaction_audit ORDER BY seq").fetchall(),
        )


@pytest.mark.parametrize("attempt", (
    "stale-different-occurrence",
    "stale-modified-request",
    "fresh-duplicate-occurrence",
))
def test_atomic_two_handle_cas_and_occurrence_replay_remain_inert(
    tmp_path, attempt: str,
) -> None:
    path = tmp_path / "synthetic-preaction.sqlite3"
    first_handle = DisconnectedAtomicPreactionLedger.create(path)
    second_handle = DisconnectedAtomicPreactionLedger(path)
    genesis = genesis_atomic_preaction_witness()
    first = first_handle.reserve(_claim("a"), retained=genesis)
    assert first.count == 1
    original_rows = _rows(path)
    assert len(original_rows[0]) == len(original_rows[1]) == 1

    if attempt == "fresh-duplicate-occurrence":
        proposal = _claim("a")
        retained = first
    elif attempt == "stale-modified-request":
        proposal = AtomicIntentClaim(
            _claim("a").occurrence_id,
            _claim("a").bound_action_id,
            "b" * 64,
        )
        retained = genesis
    else:
        proposal = _claim("b")
        retained = genesis
    with pytest.raises(AtomicPreactionRejected):
        second_handle.reserve(proposal, retained=retained)
    assert _rows(path) == original_rows

    cold = DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        cold.inspect(genesis)
    recovered = cold.inspect(first)
    assert recovered.occurrence_ids == (_claim("a").occurrence_id,)
    assert recovered.tool_dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert recovered.external_effect_proven is False
    assert recovered.trusted_approval_verified is False
    assert recovered.independent_custody_proven is False

    # An independent writer can append only with the current retained prefix.
    second = second_handle.reserve(_claim("c"), retained=first)
    assert second.count == 2
    assert len(_rows(path)[0]) == len(_rows(path)[1]) == 2
    assert DisconnectedAtomicPreactionLedger(path).inspect(
        second,
    ).automatic_replay_authorized is False
