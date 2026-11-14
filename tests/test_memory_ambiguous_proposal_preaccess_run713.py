"""Offline Memory ambiguity reviewers reject executable proposal slots pre-access.

Both reviewers are strictly read-only/manual diagnostics. Subprocess isolation
keeps imported frozen V1 classes and their descriptors unchanged for other
tests; all evidence is synthetic and no real action can be authorized.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("reviewer", ("pair", "outcome"))
@pytest.mark.parametrize(
    ("carrier", "attribute"),
    (
        ("MemoryWrite", "scope"),
        ("MemoryWrite", "source_id"),
        ("MemoryWrite", "content"),
        ("MemoryWrite", "metadata"),
        ("MemoryWrite", "expires_at_ms"),
        ("MemoryWrite", "__getattribute__"),
        ("MemoryWrite", "__new__"),
        ("MemoryWrite", "__init__"),
        ("MemoryScope", "owner_id"),
        ("MemoryScope", "namespace"),
        ("MemoryScope", "__getattribute__"),
        ("MemoryScope", "__post_init__"),
    ),
)
def test_ambiguous_reviewer_rejects_replaced_proposal_before_private_read(
    reviewer: str, carrier: str, attribute: str,
) -> None:
    script = textwrap.dedent(
        """
        from contextlib import closing
        from pathlib import Path
        import sqlite3
        from tempfile import TemporaryDirectory

        from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
        from ark.memory import ambiguous_commit_pair_review as pair
        from ark.memory import generation_cas_outcome_review as outcome
        from ark.memory.generation_fenced_cas import (
            observe_memory_generation_for_cas,
        )

        with TemporaryDirectory() as directory:
            scope = MemoryScope("local-owner", "offline")
            store = SQLiteMemoryStore(
                Path(directory) / "memory.sqlite", clock_ms=lambda: 100,
            )
            store.put(MemoryWrite(scope, "fixture", "before"))
            retained = observe_memory_generation_for_cas(store, scope, "fixture")
            proposal = MemoryWrite(scope, "fixture", "after")
            invoked = []

            def hostile(*_args, **_kwargs):
                invoked.append("untrusted callback")
                raise AssertionError("private Memory input getter executed")

            cls = {"MemoryWrite": MemoryWrite, "MemoryScope": MemoryScope}[CARRIER]
            replacement = (
                hostile if ATTRIBUTE.startswith("__") else property(hostile)
            )
            setattr(cls, ATTRIBUTE, replacement)
            try:
                if REVIEWER == "pair":
                    pair.review_memory_ambiguous_commit_pair(
                        store, proposal, retained=retained,
                    )
                else:
                    outcome.review_memory_generation_cas_outcome(
                        store, proposal, retained=retained,
                    )
            except (
                pair.MemoryAmbiguityPairRejected,
                outcome.MemoryCASOutcomeRejected,
            ) as exc:
                assert "input carrier changed" in str(exc), str(exc)
            else:
                raise AssertionError("altered input carrier accepted")
            assert invoked == []
            with closing(sqlite3.connect(store.path)) as conn:
                assert conn.execute(
                    "SELECT content,revision FROM memories"
                ).fetchone() == ("before", 1)
        """
    )
    for key, value in (
        ("CARRIER", carrier),
        ("ATTRIBUTE", attribute),
        ("REVIEWER", reviewer),
    ):
        script = script.replace(key, repr(value))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("reviewer", ("pair", "outcome"))
def test_unchanged_ambiguous_reviewer_remains_manual_only(tmp_path, reviewer):
    from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
    from ark.memory import ambiguous_commit_pair_review as pair
    from ark.memory import generation_cas_outcome_review as outcome
    from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas

    scope = MemoryScope("owner", "local")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "fixture", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "fixture")
    proposal = MemoryWrite(scope, "fixture", "after")
    if reviewer == "pair":
        receipt = pair.review_memory_ambiguous_commit_pair(
            store, proposal, retained=retained,
        )
        assert receipt.disposition == "LOCAL_UNCHANGED_REVIEW"
        assert receipt.automatic_retry_authorized is False
        assert receipt.write_authorized is False
    else:
        receipt = outcome.review_memory_generation_cas_outcome(
            store, proposal, retained=retained,
        )
        assert receipt.observation == "UNCHANGED_OBSERVED"
        assert receipt.automatic_retry_authorized is False
        assert receipt.external_action_authorized is False
