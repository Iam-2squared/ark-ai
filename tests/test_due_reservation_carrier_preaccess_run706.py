"""Due-slot fixture refuses injected witness/receipt carriers before SQLite.

Every mutation runs in a subprocess to avoid contaminating CPython slots in
other test modules. Local due records are not notification or execution grants.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    genesis_due_witness,
)


@pytest.mark.parametrize(
    ("carrier", "attribute"),
    (
        ("DueReservationWitness", "count"),
        ("DueReservationWitness", "fingerprint"),
        ("DueReservationWitness", "__getattribute__"),
        ("DueReservationWitness", "__new__"),
        ("DueReservationWitness", "independent_custody_proven"),
        ("DueReservationReceipt", "occurrence_id"),
        ("DueReservationReceipt", "reserved_at_ms"),
        ("DueReservationReceipt", "witness"),
        ("DueReservationReceipt", "__getattribute__"),
        ("DueReservationReceipt", "__new__"),
        ("DueReservationReceipt", "automatic_replay_authorized"),
        ("DueReservationReceipt", "trusted_clock_verified"),
    ),
)
def test_mutated_carrier_cannot_read_or_persist_due_reservation(
    carrier, attribute,
):
    script = textwrap.dedent(
        """
        import contextlib
        import sqlite3
        import tempfile
        from pathlib import Path

        import ark.agency.disconnected_due_reservation as module

        with tempfile.TemporaryDirectory() as location:
            path = Path(location) / "due.sqlite"
            store = module.DisconnectedDueReservations(path)
            retained = module.genesis_due_witness()
            calls = []

            def hostile(*args, **kwargs):
                calls.append("untrusted-carrier-executed")
                raise AssertionError("hostile callback executed")

            kind = getattr(module, CARRIER)
            if ATTRIBUTE.startswith("__"):
                setattr(kind, ATTRIBUTE, hostile)
            else:
                setattr(kind, ATTRIBUTE, property(hostile))
            try:
                store.reserve_due(
                    policy_sha256="a" * 64, due_at_ms=100,
                    observed_now_ms=100, retained=retained,
                )
            except module.DueReservationRejected:
                pass
            else:
                raise AssertionError("untrusted due carrier was accepted")
            assert not calls, calls
            with contextlib.closing(sqlite3.connect(path)) as connection:
                assert connection.execute(
                    "SELECT COUNT(*) FROM due_reservations"
                ).fetchone() == (0,)
        """
    )
    script = script.replace("CARRIER", repr(carrier))
    script = script.replace("ATTRIBUTE", repr(attribute))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_original_due_carriers_remain_inert_after_restart(tmp_path):
    path = tmp_path / "healthy-due.sqlite"
    store = DisconnectedDueReservations(path)
    retained = genesis_due_witness()
    receipt = store.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=100,
        observed_now_ms=100,
        retained=retained,
    )
    assert receipt.witness.count == 1
    assert receipt.notification_authorized is False
    assert receipt.execution_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    restarted = DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert restarted.witness() == receipt.witness
