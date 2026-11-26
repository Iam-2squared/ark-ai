"""Original quarantine receipt slots must be checked before local COMMIT.

Disposable SQLite fixtures only. No dispatch, notifications, clock authority,
automatic retry, or consent comes from a quarantine receipt.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize(
    "mutation",
    (
        "class", "witness", "quarantined_index", "__init__",
        "__new__", "__getattribute__", "__getattr__",
    ),
)
def test_installed_receipt_mutation_denied_before_quarantine_write(
    mutation: str,
) -> None:
    script = textwrap.dedent(
        """
        import contextlib
        import sqlite3
        import tempfile
        from pathlib import Path

        import ark.disconnected_schedule_quarantine_ledger as quarantine

        with tempfile.TemporaryDirectory() as directory:
            policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
            path = Path(directory) / "quarantine.sqlite"
            ledger = quarantine.DisconnectedScheduleQuarantineLedger(
                path, policy=policy, create=True,
            )
            retained = quarantine.genesis_quarantine_witness(policy)
            occurrence = quarantine.derive_quarantined_occurrence(policy, 0)
            called = []

            def hostile(*_args, **_kwargs):
                called.append(True)
                raise AssertionError("hostile receipt field or constructor invoked")

            if MUTATION == "class":
                class Counterfeit:
                    def __init__(self, *_args):
                        hostile()
                quarantine.QuarantineReceipt = Counterfeit
            elif MUTATION.startswith("__"):
                setattr(quarantine.QuarantineReceipt, MUTATION, hostile)
            else:
                setattr(quarantine.QuarantineReceipt, MUTATION, property(hostile))

            try:
                ledger.quarantine_expired(
                    index=0, occurrence_id=occurrence,
                    observed_ms=10_501, retained=retained,
                )
            except quarantine.ScheduleQuarantineRejected as exc:
                assert "receipt constructor or field descriptor changed" in str(exc)
            else:
                raise AssertionError("tampered receipt was accepted")
            assert called == [], called
            with contextlib.closing(sqlite3.connect(path)) as connection:
                assert connection.execute(
                    "SELECT COUNT(*) FROM quarantines"
                ).fetchone() == (0,)
        """
    ).replace("MUTATION", repr(mutation))
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True,
        text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def test_receipt_getter_installed_during_digest_rolls_back(tmp_path, monkeypatch):
    import sqlite3
    from contextlib import closing

    import ark.disconnected_schedule_quarantine_ledger as quarantine

    policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    path = tmp_path / "digest-callback.sqlite"
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    retained = quarantine.genesis_quarantine_witness(policy)
    occurrence = quarantine.derive_quarantined_occurrence(policy, 0)
    original_digest = quarantine._digest
    invoked = []

    def hostile(_self):
        invoked.append(True)
        raise AssertionError("receipt descriptor executed")

    def reentrant_digest(payload):
        if payload[0] == "row":
            monkeypatch.setattr(
                quarantine.QuarantineReceipt, "witness", property(hostile),
            )
        return original_digest(payload)

    with monkeypatch.context() as patch:
        patch.setattr(quarantine, "_digest", reentrant_digest)
        with pytest.raises(
            quarantine.ScheduleQuarantineRejected,
            match="receipt constructor or field descriptor changed",
        ):
            ledger.quarantine_expired(
                index=0, occurrence_id=occurrence,
                observed_ms=10_501, retained=retained,
            )
    assert invoked == []
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM quarantines"
        ).fetchone() == (0,)


def test_original_quarantine_receipt_remains_denial_only(tmp_path):
    import ark.disconnected_schedule_quarantine_ledger as quarantine

    policy = quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        tmp_path / "normal.sqlite", policy=policy, create=True,
    )
    receipt = ledger.quarantine_expired(
        index=0,
        occurrence_id=quarantine.derive_quarantined_occurrence(policy, 0),
        observed_ms=10_501,
        retained=quarantine.genesis_quarantine_witness(policy),
    )
    assert receipt.quarantined_index == 0
    assert receipt.witness.count == 1
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    assert receipt.consent_verified is False
