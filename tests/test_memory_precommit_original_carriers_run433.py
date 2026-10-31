"""Memory CAS must reject equal-value caller retargeting before SQLite COMMIT.

Only disposable local SQLite is used. A rolled-back row must not leave an
orphan audit event, and a rejected update must not replace the old revision.
"""

import pytest

from ark.memory import (
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def _replace_equal_value(write, field):
    target = write.scope if field in ("owner_id", "namespace") else write
    original = getattr(target, field)
    if field == "expires_at_ms":
        replacement = int(str(original))
    else:
        middle = len(original) // 2
        replacement = "".join((original[:middle], original[middle:]))
    assert replacement == original
    assert replacement is not original
    object.__setattr__(target, field, replacement)


@pytest.mark.parametrize("operation", ("create", "update"))
@pytest.mark.parametrize("phase", ("clock", "event"))
@pytest.mark.parametrize(
    "field", ("owner_id", "namespace", "source_id", "content", "expires_at_ms"),
)
def test_put_rejects_original_carrier_replacement_before_commit(
    tmp_path, operation, phase, field,
):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("offline-test-owner", "private-notes")
    if operation == "update":
        initial = store.put(
            MemoryWrite(scope, "source-identity", "old-content"),
        )
        assert initial.revision == 1
    write = MemoryWrite(
        scope, "source-identity", "new-value-that-is-local",
        expires_at_ms=5_000_001,
    )

    def sabotage():
        _replace_equal_value(write, field)
        return 2000

    if phase == "clock":
        store._clock_ms = sabotage
    else:
        original_event = store._event

        def event_then_sabotage(*args):
            original_event(*args)
            _replace_equal_value(write, field)

        store._event = event_then_sabotage

    with pytest.raises(
        MemorySchemaError, match="memory write changed",
    ):
        store.put(write, expected_revision=1 if operation == "update" else 0)

    # A failure before COMMIT must roll back the row AND audit event.
    reopened = SQLiteMemoryStore(
        tmp_path / "memory.sqlite", clock_ms=lambda: 2500,
    )
    current = reopened.get(
        reopened.events(scope)[0].memory_id, scope,
        include_expired=True,
    ) if operation == "update" else None
    if operation == "create":
        assert reopened.events(scope) == []
        assert current is None
    else:
        assert current is not None
        assert current.revision == 1
        assert current.content == "old-content"
        assert [(e.operation, e.revision) for e in reopened.events(scope)] == [
            ("create", 1),
        ]
