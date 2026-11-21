"""A substituted proactive witness schema reader must never inspect local rows.

The test has no notification, dispatch, real scheduler or trusted clock.
"""

from __future__ import annotations

import pytest

from ark import proactive_synthetic_continuity_review as continuity
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerRejected,
)


def _ledger(tmp_path):
    return SyntheticProactiveLedger(tmp_path / "prepared.sqlite")


@pytest.mark.parametrize("retained", (False, True))
def test_hostile_schema_callback_rejected_before_private_sqlite(
    tmp_path, monkeypatch, retained,
):
    ledger = _ledger(tmp_path)
    previous = continuity.read_proactive_witness(ledger) if retained else None
    executed = []

    def hostile(conn):
        executed.append(conn)
        raise AssertionError("unreviewed schema callback received SQLite handle")

    with monkeypatch.context() as patch:
        patch.setattr(continuity, "_validate", hostile)
        with pytest.raises(
            SyntheticTriggerRejected,
            match="proactive witness carrier changed before private history access",
        ):
            continuity.read_proactive_witness(ledger, retained=previous)
        assert executed == []
    healthy = continuity.read_proactive_witness(ledger, retained=previous)
    assert healthy.row_hashes == ()
    assert healthy.digest.startswith("synthetic_triggers_")


def test_schema_rebinding_during_path_resolution_is_denied_before_db_read(
    tmp_path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    original_resolve = type(ledger.path).resolve
    touched = []
    leaked = []

    def hostile(conn):
        leaked.append(conn)
        raise AssertionError("schema callback executed with private connection")

    with monkeypatch.context() as patch:
        def rebind_during_resolve(self, *args, **kwargs):
            value = original_resolve(self, *args, **kwargs)
            if self == ledger.path and not touched:
                touched.append(True)
                patch.setattr(continuity, "_validate", hostile)
            return value

        patch.setattr(type(ledger.path), "resolve", rebind_during_resolve)
        with pytest.raises(
            SyntheticTriggerRejected,
            match="proactive witness carrier changed before private history access",
        ):
            continuity.read_proactive_witness(ledger)
    assert touched == [True]
    assert leaked == []
    assert continuity.read_proactive_witness(ledger).row_hashes == ()
