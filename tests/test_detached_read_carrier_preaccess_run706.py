"""Synthetic READ journal receipts reject replaced slots before field access.

Hostile class mutations are exercised in separate interpreters: modifying
CPython dataclass type slots can persist beyond monkeypatch restoration.
All payloads here are deterministic disconnected digests, not real READs.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadReceipt,
    genesis_witness,
)

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16
_DIGEST = "c" * 64


@pytest.mark.parametrize(
    ("carrier", "attribute", "entry"),
    (
        ("ReadJournalWitness", "count", "module._check_witness(witness)"),
        ("ReadJournalWitness", "tip_sha256", "module._check_witness(witness)"),
        ("ReadJournalWitness", "__getattribute__", "module._check_witness(witness)"),
        ("ReadJournalWitness", "replay_authorized", "module._check_witness(witness)"),
        ("ReadReceipt", "request_id", "module._check_receipt(receipt)"),
        ("ReadReceipt", "input_digest", "module._check_receipt(receipt)"),
        ("ReadReceipt", "__getattribute__", "module._check_receipt(receipt)"),
        ("ReadReceipt", "__init__", "module._check_receipt(receipt)"),
        ("ReadJournalWitness", "__init__", "module.genesis_witness()"),
        ("ReadJournalWitness", "__new__", "module.genesis_witness()"),
    ),
)
def test_mutated_carrier_never_executes_hostile_slot(carrier, attribute, entry):
    script = textwrap.dedent(
        """
        import ark.agency.disconnected_read_journal as module

        receipt = module.ReadReceipt(
            "req_" + "a" * 32, "step_" + "1" * 16,
            "math.sum", "c" * 64, "d" * 64,
        )
        witness = module.genesis_witness()
        calls = []

        def hostile(*args, **kwargs):
            calls.append("private-carrier-access")
            raise AssertionError("hostile callback executed")

        carrier = getattr(module, CARRIER)
        if ATTRIBUTE.startswith("__"):
            setattr(carrier, ATTRIBUTE, hostile)
        else:
            setattr(carrier, ATTRIBUTE, property(hostile))

        try:
            ENTRY
        except module.ReadJournalRejected:
            pass
        else:
            raise AssertionError("mutated carrier was accepted")
        assert not calls, calls
        """
    )
    script = script.replace("CARRIER", repr(carrier))
    script = script.replace("ATTRIBUTE", repr(attribute))
    script = script.replace("ENTRY", entry)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_unmodified_carriers_still_allow_bounded_disconnected_recovery(tmp_path):
    path = tmp_path / "synthetic-reads.sqlite"
    row = ReadReceipt(_REQUEST, _STEP, "math.sum", _DIGEST, "d" * 64)
    with DisconnectedReadJournal.create(path) as journal:
        genesis = genesis_witness()
        assert journal.verify(genesis) == genesis
        updated = journal.append(row, genesis)
        recovered = journal.recover_receipts(updated)
        assert recovered.receipts == (row,)
        assert recovered.witness == updated
        assert recovered.dispatch_authorized is False
        assert recovered.automatic_replay_authorized is False

    with DisconnectedReadJournal.open(path) as reopened:
        again = reopened.recover_receipts(updated)
        assert again.receipts == (row,)
        assert again.witness == updated
