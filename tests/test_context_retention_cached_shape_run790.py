"""Privacy recheck rejects forged or oversized cached inventory before SQLite.

Synthetic Memory and revocation stores only; no erasure or disclosure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
    review_synthetic_retention_recheck,
)
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


class EqualStr(str):
    """Value-equal text subclass cannot replace an exact receipt field."""


def _fixture(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "notes")
    memory.put(MemoryWrite(
        scope, "fixture-source", "synthetic private text", expires_at_ms=150,
    ))
    revocations = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
    )
    return memory, scope, revocations, cached


@pytest.mark.parametrize("mutation", (
    "scope_digest_subclass", "inventory_digest_subclass", "inventory_digest_invalid",
    "revoked_integer", "items_over_budget", "revision_overflow",
))
def test_malformed_cached_receipt_refused_without_private_memory_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    memory, scope, revocations, cached = _fixture(tmp_path)
    if mutation == "scope_digest_subclass":
        object.__setattr__(cached, "scope_digest", EqualStr(cached.scope_digest))
    elif mutation == "inventory_digest_subclass":
        object.__setattr__(cached, "inventory_digest", EqualStr(cached.inventory_digest))
    elif mutation == "inventory_digest_invalid":
        object.__setattr__(cached, "inventory_digest", "retention_" + "g" * 64)
    elif mutation == "revoked_integer":
        object.__setattr__(cached, "revoked", int(cached.revoked))
    elif mutation == "items_over_budget":
        object.__setattr__(cached, "items", cached.items * 1001)
    else:
        object.__setattr__(cached.items[0], "revision", 1 << 63)

    opened: list[str] = []

    def forbidden_open(_self: SQLiteMemoryStore) -> object:
        opened.append("private-memory")
        raise AssertionError("malformed cached receipt reached Memory SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", forbidden_open)
        with pytest.raises(
            SyntheticRetentionRecheckRejected, match="exact cached retention",
        ):
            review_synthetic_retention_recheck(
                memory, scope, revocations, cached, now_ms=101, max_age_ms=10,
            )
    assert opened == []


def test_bounded_original_retention_recheck_stays_deny_only(tmp_path: Path) -> None:
    memory, scope, revocations, cached = _fixture(tmp_path)
    result = review_synthetic_retention_recheck(
        memory, scope, revocations, cached, now_ms=150, max_age_ms=100,
    )
    assert len(result.expired_memory_ids) == 1
    assert result.scope_revoked is False
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
