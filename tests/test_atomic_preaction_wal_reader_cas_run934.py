"""WAL snapshot cannot launder a stale disconnected pre-action witness.

A reader that began before a second atomic intent+audit commit may still see
its old coherent snapshot. That must not be used to authorize a new CAS or
interpret an ambiguous WRITE as executed. Only temporary local SQLite.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(seed: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize("uri_reader", (False, True))
def test_stale_wal_reader_keeps_coherent_pair_but_not_cas_authority(
    tmp_path, uri_reader: bool,
) -> None:
    path = tmp_path / "atomic-wal-reader.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    first = ledger.reserve(
        _claim("a"), retained=genesis_atomic_preaction_witness(),
    )
    reader_target = path.as_uri() + "?mode=ro" if uri_reader else str(path)
    with closing(
        sqlite3.connect(reader_target, uri=uri_reader, timeout=5),
    ) as reader:
        reader.execute("BEGIN")
        assert reader.execute(
            "SELECT COUNT(*) FROM intents",
        ).fetchone() == (1,)
        assert reader.execute(
            "SELECT COUNT(*) FROM preaction_audit",
        ).fetchone() == (1,)

        second = DisconnectedAtomicPreactionLedger(path).reserve(
            _claim("d"), retained=first,
        )
        assert second.count == 2
        # SQLite WAL preserves the original snapshot for the old reader.
        assert reader.execute(
            "SELECT COUNT(*) FROM intents",
        ).fetchone() == (1,)
        assert reader.execute(
            "SELECT COUNT(*) FROM preaction_audit",
        ).fetchone() == (1,)

        cold = DisconnectedAtomicPreactionLedger(path)
        with pytest.raises(AtomicPreactionRejected):
            cold.inspect(first)
        with pytest.raises(AtomicPreactionRejected):
            cold.reserve(_claim("e"), retained=first)
        current = cold.inspect(second)
        assert current.occurrence_ids == (
            _claim("a").occurrence_id, _claim("d").occurrence_id,
        )
        assert current.tool_dispatch_authorized is False
        assert current.automatic_replay_authorized is False
        assert current.external_effect_proven is False

    after = DisconnectedAtomicPreactionLedger(path).inspect(second)
    assert after.occurrence_ids == current.occurrence_ids
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM intents",
        ).fetchone() == (2,)
        assert conn.execute(
            "SELECT COUNT(*) FROM preaction_audit",
        ).fetchone() == (2,)
