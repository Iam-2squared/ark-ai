"""Retained Memory JSON is bounded before platform-specific recursive parsing."""

from __future__ import annotations

import json
import sqlite3

import pytest

import ark.memory.disconnected_witness_ledger as witness
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview


@pytest.mark.parametrize("open_char,close_char", [("[", "]"), ("{", "}")])
@pytest.mark.parametrize("depth", [65, 1400])
def test_hostile_nested_witness_is_rejected_by_depth_budget(
    open_char, close_char, depth,
):
    raw = open_char * depth + close_char * depth
    with pytest.raises(witness.MemoryWitnessLedgerRejected, match="nesting budget"):
        witness._decoded(raw)


def test_short_valid_epoch_round_trips_without_changing_schema():
    review = AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
    )
    assert witness._decoded(witness._payload(review)) == review


def test_brackets_inside_escaped_json_string_are_not_counted_as_containers():
    raw = "[" + json.dumps('"' + "[" * 200) + "]"
    with pytest.raises(
        witness.MemoryWitnessLedgerRejected, match="invalid witness epoch structure",
    ):
        witness._decoded(raw)


def test_malformed_quoted_brackets_are_not_authorized(tmp_path):
    store = witness.DisconnectedMemoryWitnessLedger(
        tmp_path / "retained.sqlite", create=True,
    )
    genesis = witness.genesis_memory_ledger_witness()
    with pytest.raises(witness.MemoryWitnessLedgerRejected):
        witness._decoded('["\\\"' + "[" * 70)


def test_persisted_overdeep_epoch_is_rejected_through_readonly_inspect(tmp_path):
    path = tmp_path / "retained.sqlite"
    store = witness.DisconnectedMemoryWitnessLedger(path, create=True)
    genesis = witness.genesis_memory_ledger_witness()
    payload = "[" * 65 + "]" * 65
    chain = witness._digest((
        "epoch", genesis.chain_sha256, 1, payload,
        "BASELINE_UNAUTHENTICATED",
    ))
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO retained_memory_epochs VALUES (?,?,?,?)",
            (1, payload, "BASELINE_UNAUTHENTICATED", chain),
        )
    with pytest.raises(witness.MemoryWitnessLedgerRejected, match="nesting budget"):
        store.inspect(retained=genesis)
