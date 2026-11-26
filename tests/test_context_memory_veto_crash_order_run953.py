"""Run953: separate Memory and privacy-veto commits survive an abrupt exit.

A later local inventory is not a coherent cross-store snapshot, proof of
erasure, authenticated revocation, or permission to reuse private context.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.personal_context_retention_review import (
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("revocation_first", (False, True))
def test_cold_privacy_veto_survives_memory_commit_order_and_process_exit(
    tmp_path, revocation_first: bool,
) -> None:
    memory_path = tmp_path / "local-memory.sqlite3"
    veto_path = tmp_path / "local-private-veto.sqlite3"

    script = """
import os
import sys
from pathlib import Path
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger
private = MemoryScope("synthetic-owner", "private")
public = MemoryScope("synthetic-owner", "public")
memory = SQLiteMemoryStore(Path(sys.argv[1]), clock_ms=lambda: 100)
veto = SyntheticContextRevocationLedger(Path(sys.argv[2]))
if sys.argv[3] == "veto-first":
    veto.revoke(private, at_ms=120)
memory.put(MemoryWrite(private, "source", "PRIVATE_CRASH_FIXTURE_SENTINEL"))
memory.put(MemoryWrite(public, "source", "PUBLIC_CRASH_FIXTURE"))
if sys.argv[3] == "memory-first":
    veto.revoke(private, at_ms=120)
os._exit(47)
"""
    result = subprocess.run(
        [
            sys.executable, "-c", script, str(memory_path), str(veto_path),
            "veto-first" if revocation_first else "memory-first",
        ],
        text=True, capture_output=True, check=False, timeout=30,
    )
    assert result.returncode == 47, result.stderr

    private = MemoryScope("synthetic-owner", "private")
    public = MemoryScope("synthetic-owner", "public")
    memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 200)
    veto = SyntheticContextRevocationLedger(veto_path, require_existing=True)
    private_review = review_synthetic_retention_inventory(
        memory, private, veto, now_ms=200,
    )
    public_review = review_synthetic_retention_inventory(
        memory, public, veto, now_ms=200,
    )

    assert private_review.revoked is True
    assert public_review.revoked is False
    assert len(private_review.items) == len(public_review.items) == 1
    assert private_review.context_use_authorized is False
    assert private_review.deletion_authorized is False
    assert private_review.erasure_completed is False
    assert public_review.context_use_authorized is False
    with pytest.raises(SyntheticContextRevocationRejected):
        veto.assert_not_revoked((private,))
    veto.assert_not_revoked((public,))

    # A review must not edit the durable Memory or privacy-veto rows.
    with sqlite3.connect(memory_path) as conn:
        before_memory = conn.execute(
            "SELECT memory_id,owner_id,namespace,revision FROM memories "
            "ORDER BY namespace"
        ).fetchall()
    with sqlite3.connect(veto_path) as conn:
        before_veto = conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
    assert len(before_memory) == 2
    assert len(before_veto) == 1
    assert before_veto[0][1] == 120
    assert "PRIVATE_CRASH_FIXTURE_SENTINEL" not in repr(private_review)
    assert "PRIVATE_CRASH_FIXTURE_SENTINEL" not in repr(public_review)

    review_synthetic_retention_inventory(memory, private, veto, now_ms=201)
    with sqlite3.connect(memory_path) as conn:
        assert conn.execute(
            "SELECT memory_id,owner_id,namespace,revision FROM memories "
            "ORDER BY namespace"
        ).fetchall() == before_memory
    with sqlite3.connect(veto_path) as conn:
        assert conn.execute(
            "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall() == before_veto
