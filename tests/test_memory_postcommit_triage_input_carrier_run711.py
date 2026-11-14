"""Uncertain-COMMIT Memory triage rejects executable input carriers pre-access.

The frozen V1 input classes are patched only in an isolated interpreter.
No retry, external action, real context, or consent is authorized.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize(
    ("carrier", "attribute"),
    (
        ("MemoryWrite", "scope"),
        ("MemoryWrite", "source_id"),
        ("MemoryWrite", "content"),
        ("MemoryWrite", "metadata"),
        ("MemoryWrite", "expires_at_ms"),
        ("MemoryWrite", "__init__"),
        ("MemoryWrite", "__new__"),
        ("MemoryWrite", "__getattribute__"),
        ("MemoryWrite", "__post_init__"),
        ("MemoryScope", "owner_id"),
        ("MemoryScope", "namespace"),
        ("MemoryScope", "__init__"),
        ("MemoryScope", "__new__"),
        ("MemoryScope", "__getattribute__"),
        ("MemoryScope", "__post_init__"),
    ),
)
def test_triage_rejects_original_carrier_substitution_before_getter_or_sqlite(
    carrier: str, attribute: str,
) -> None:
    script = textwrap.dedent(
        """
        import contextlib
        import sqlite3
        import tempfile
        from pathlib import Path

        from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
        from ark.memory.generation_fenced_cas import (
            observe_memory_generation_for_cas,
        )
        from ark.memory.postcommit_uncertainty_review import (
            MemoryCommitTriageRejected, review_uncertain_memory_commit,
        )

        with tempfile.TemporaryDirectory() as directory:
            scope = MemoryScope("owner", "private")
            store = SQLiteMemoryStore(
                Path(directory) / "mem.sqlite", clock_ms=lambda: 100,
            )
            store.put(MemoryWrite(scope, "source", "before"))
            retained = observe_memory_generation_for_cas(
                store, scope, "source",
            )
            proposal = MemoryWrite(scope, "source", "after")
            called = []

            def hostile(*_args, **_kwargs):
                called.append("hostile")
                raise AssertionError("hostile input or SQLite access")

            # A direct SQLite read should be unnecessary for a known-unsafe
            # class definition. Avoid patching frozen input classes in pytest.
            SQLiteMemoryStore._connect_readonly = hostile
            target = {"MemoryWrite": MemoryWrite, "MemoryScope": MemoryScope}[CARRIER]
            if ATTRIBUTE.startswith("__"):
                setattr(target, ATTRIBUTE, hostile)
            else:
                setattr(target, ATTRIBUTE, property(hostile))
            try:
                review_uncertain_memory_commit(
                    store, proposal, retained_before=retained,
                )
            except MemoryCommitTriageRejected as exc:
                assert "input carrier changed" in str(exc), str(exc)
            else:
                raise AssertionError("mutated input class accepted")
            assert called == [], called
            with contextlib.closing(sqlite3.connect(store.path)) as conn:
                assert conn.execute(
                    "SELECT content, revision FROM memories"
                ).fetchone() == ("before", 1)
        """
    )
    script = script.replace("CARRIER", repr(carrier))
    script = script.replace("ATTRIBUTE", repr(attribute))
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True,
        text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
