"""Do not return a forged CAS record after a successful SQLite COMMIT."""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


class _CommitExitHook:
    def __init__(self, connection, after_commit):
        self._connection = connection
        self._after_commit = after_commit

    def __getattr__(self, key):
        return getattr(self._connection, key)

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, kind, error, traceback):
        result = self._connection.__exit__(kind, error, traceback)
        if kind is None:
            self._after_commit()
        return result

    def close(self):
        self._connection.close()


@pytest.mark.parametrize(
    ("target", "field", "new_value"),
    [
        ("record", "content", "forged"),
        ("record", "revision", 99),
        ("record", "content_sha256", "0" * 64),
        ("record", "metadata", {"source": "forged"}),
        ("token", "row_sha256", "0" * 64),
        ("token", "last_event_id", 999),
    ],
)
def test_commit_exit_mutation_requires_manual_review(
    tmp_path, monkeypatch, target, field, new_value,
):
    store = SQLiteMemoryStore(tmp_path / "commit-cas.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("offline-owner", "private")
    initial = store.put(
        MemoryWrite(scope, "stable", "original"), expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    original_snapshot = cas._snapshot
    observed = []

    def record_snapshot(*args):
        row, token = original_snapshot(*args)
        observed.append((row, token))
        return row, token

    original_connect = store._connect

    def after_commit():
        # _snapshot runs once before UPDATE and once after. The latter is
        # the returned record. COMMIT is complete before tampering occurs.
        assert len(observed) == 2
        row, token = observed[-1]
        object.__setattr__(
            row if target == "record" else token, field, new_value,
        )

    monkeypatch.setattr(cas, "_snapshot", record_snapshot)
    monkeypatch.setattr(
        store, "_connect",
        lambda: _CommitExitHook(original_connect(), after_commit),
    )
    with pytest.raises(
        cas.MemoryGenerationCASRejected, match="post-COMMIT result uncertain",
    ):
        cas.generation_fenced_memory_update(
            store, MemoryWrite(scope, "stable", "updated"), retained=retained,
        )
    # The raised exception is not a rollback signal or retry permission.
    saved = store.get(initial.memory_id, scope, include_expired=True)
    assert saved.content == "updated"
    assert saved.revision == 2
    assert [event.operation for event in store.events(scope)] == [
        "create", "update",
    ]


def test_normal_commit_still_returns_persisted_record(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "normal-cas.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("offline-owner", "private")
    saved = store.put(
        MemoryWrite(scope, "stable", "original"), expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    updated = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "stable", "updated"), retained=retained,
    )
    assert updated.content == "updated"
    assert updated.revision == 2
    assert store.get(saved.memory_id, scope).content == "updated"
