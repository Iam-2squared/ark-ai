"""Proactive historical witness slots are checked before private access.

Class-level mutations of frozen dataclasses are isolated in child processes to
avoid CPython inherited-__new__ slot poisoning between otherwise healthy tests.
All fixtures are disconnected: no notification, consent, or real execution.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark.proactive_synthetic_continuity_review import (
    assert_proactive_history_continues,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import SyntheticProactiveLedger


@pytest.mark.parametrize(
    "attribute",
    ("row_hashes", "digest", "__init__", "__new__",
     "__getattribute__", "__getattr__"),
)
@pytest.mark.parametrize("entrypoint", ("direct", "read"))
def test_original_witness_slots_block_hostile_lookup_preaccess(
    attribute, entrypoint,
):
    script = textwrap.dedent(
        """
        import tempfile
        from pathlib import Path

        import ark.proactive_synthetic_continuity_review as continuity
        from ark.proactive_synthetic_review import (
            SyntheticProactiveLedger,
            SyntheticTriggerRejected,
        )

        with tempfile.TemporaryDirectory() as location:
            ledger = SyntheticProactiveLedger(Path(location) / "triggers.sqlite")
            witness = continuity.read_proactive_witness(ledger)
            called = []

            def hostile(*args, **kwargs):
                called.append("hostile witness getter/constructor")
                raise AssertionError("private witness callback executed")

            cls = continuity.SyntheticTriggerWitness
            setattr(
                cls, ATTRIBUTE,
                property(hostile) if ATTRIBUTE in ("row_hashes", "digest")
                else hostile,
            )

            def forbidden_sqlite(*args, **kwargs):
                called.append("SQLite opened before original-slot check")
                raise AssertionError("SQLite accessed before witness preflight")

            continuity.sqlite3.connect = forbidden_sqlite
            try:
                if ENTRYPOINT == "direct":
                    continuity.assert_proactive_history_continues(witness, witness)
                else:
                    continuity.read_proactive_witness(ledger, retained=witness)
            except SyntheticTriggerRejected as error:
                assert "carrier changed" in str(error), str(error)
            else:
                raise AssertionError("substituted witness admitted")
            assert not called, called
        """
    ).replace("ATTRIBUTE", repr(attribute)).replace(
        "ENTRYPOINT", repr(entrypoint)
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_healthy_proactive_witness_remains_readonly_and_non_authorizing(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "healthy.sqlite")
    old = read_proactive_witness(ledger)
    new = read_proactive_witness(ledger, retained=old)
    assert_proactive_history_continues(old, new)
    assert old == new
    assert ledger.count() == 0
