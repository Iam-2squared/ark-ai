"""Opt-in Memory generation-CAS must reject hostile class hooks before I/O.

Subprocess isolation preserves frozen V1 dataclass contracts in the main test
process. All contents are dummy local fixtures; no external action or consent.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize(
    ("carrier", "attribute", "operation"),
    (
        ("MemoryWrite", "scope", "update"),
        ("MemoryWrite", "source_id", "update"),
        ("MemoryWrite", "content", "update"),
        ("MemoryWrite", "metadata", "update"),
        ("MemoryWrite", "expires_at_ms", "update"),
        ("MemoryWrite", "__getattribute__", "update"),
        ("MemoryWrite", "__init__", "update"),
        ("MemoryWrite", "__new__", "update"),
        ("MemoryScope", "owner_id", "observe"),
        ("MemoryScope", "namespace", "observe"),
        ("MemoryScope", "__getattribute__", "observe"),
        ("MemoryScope", "__post_init__", "update"),
        ("MemoryScope", "__new__", "observe"),
    ),
)
def test_original_cas_carrier_guard_rejects_before_content_or_sqlite(
    carrier, attribute, operation,
):
    script = textwrap.dedent(
        """
        import contextlib
        import sqlite3
        import tempfile
        from pathlib import Path

        import ark.memory.generation_fenced_cas as cas
        from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

        with tempfile.TemporaryDirectory() as directory:
            scope = MemoryScope("owner", "private")
            store = SQLiteMemoryStore(
                Path(directory) / "mem.sqlite", clock_ms=lambda: 100,
            )
            store.put(MemoryWrite(scope, "source", "before"))
            retained = cas.observe_memory_generation_for_cas(
                store, scope, "source",
            )
            proposal = MemoryWrite(scope, "source", "after")
            invoked = []

            def hostile(*args, **kwargs):
                invoked.append("private-input-access")
                raise AssertionError("hostile getter or constructor invoked")

            kind = {"MemoryWrite": MemoryWrite, "MemoryScope": MemoryScope}[CARRIER]
            if ATTRIBUTE.startswith("__"):
                setattr(kind, ATTRIBUTE, hostile)
            else:
                setattr(kind, ATTRIBUTE, property(hostile))

            try:
                if OPERATION == "observe":
                    cas.observe_memory_generation_for_cas(store, scope, "source")
                else:
                    cas.generation_fenced_memory_update(
                        store, proposal, retained=retained,
                    )
            except cas.MemoryGenerationCASRejected:
                pass
            else:
                raise AssertionError("mutated Memory input accepted")
            assert not invoked, invoked
            with contextlib.closing(sqlite3.connect(store.path)) as connection:
                assert connection.execute(
                    "SELECT content,revision FROM memories"
                ).fetchone() == ("before", 1)
        """
    )
    for key, value in (
        ("CARRIER", carrier),
        ("ATTRIBUTE", attribute),
        ("OPERATION", operation),
    ):
        script = script.replace(key, repr(value))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_unmodified_optional_generation_cas_updates_only_local_row(tmp_path):
    scope = MemoryScope("owner", "private")
    store = SQLiteMemoryStore(
        tmp_path / "healthy.sqlite", clock_ms=lambda: 100,
    )
    store.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    updated = generation_fenced_memory_update(
        store, MemoryWrite(scope, "source", "after"), retained=retained,
    )
    assert updated.content == "after"
    assert updated.revision == 2
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False
