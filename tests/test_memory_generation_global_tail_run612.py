"""Generation-fenced CAS refuses unrelated event-log tail corruption.

Local disposable SQLite fixtures only. Dense AUTOINCREMENT history is a
consistency invariant, not independent writer authentication or consent.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


def _setup(tmp_path, *, other_first=False):
    store = SQLiteMemoryStore(
        tmp_path / "generation-global-tail.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("fixture-owner", "private")
    if other_first:
        other = store.put(MemoryWrite(scope, "other", "other"))
        primary = store.put(MemoryWrite(scope, "primary", "primary"))
    else:
        primary = store.put(MemoryWrite(scope, "primary", "primary"))
        other = store.put(MemoryWrite(scope, "other", "other"))
    token = cas.observe_memory_generation_for_cas(store, scope, "primary")
    return store, scope, primary, other, token


@pytest.mark.parametrize("scenario", (
    "delete_prior_unrelated",
    "delete_later_unrelated",
    "erase_other_lifetime",
    "delete_all",
    "sequence_rewind",
    "sequence_advance",
    "sequence_delete",
))
def test_unrelated_event_gap_or_highwater_blocks_observation_and_cas(
    tmp_path, scenario,
):
    store, scope, primary, other, token = _setup(
        tmp_path, other_first=scenario == "delete_prior_unrelated",
    )
    if scenario == "erase_other_lifetime":
        assert store.delete(other.memory_id, scope, expected_revision=1)

    with sqlite3.connect(store.path) as conn:
        if scenario in ("delete_prior_unrelated", "delete_later_unrelated"):
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=?", (other.memory_id,),
            )
        elif scenario == "erase_other_lifetime":
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=?", (other.memory_id,),
            )
        elif scenario == "delete_all":
            conn.execute("DELETE FROM memory_events")
        elif scenario == "sequence_rewind":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=1 WHERE name='memory_events'"
            )
        elif scenario == "sequence_advance":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=50 WHERE name='memory_events'"
            )
        else:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='memory_events'"
            )
    with sqlite3.connect(store.path) as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone()[0]
    with pytest.raises(cas.MemoryGenerationCASRejected, match="high-water"):
        cas.observe_memory_generation_for_cas(store, scope, "primary")
    with pytest.raises(cas.MemoryGenerationCASRejected, match="high-water"):
        cas.generation_fenced_memory_update(
            store, MemoryWrite(scope, "primary", "not committed"),
            retained=token,
        )
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone()[0] == before
    assert store.get(primary.memory_id, scope).revision == 1


def test_valid_other_row_append_does_not_block_cas(tmp_path):
    store, scope, primary, _other, token = _setup(tmp_path)
    result = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "primary", "updated"), retained=token,
    )
    assert result.memory_id == primary.memory_id
    assert result.revision == 2
    assert store.get(primary.memory_id, scope).content == "updated"
