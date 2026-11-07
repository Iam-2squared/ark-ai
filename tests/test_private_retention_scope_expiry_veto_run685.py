"""A local privacy veto is scoped and survives Memory expiry and restart.

Retained hashes are local continuity diagnostics; no returned inventory may
prove user consent, deletion of backups, or authorized context disclosure.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _deny(report):
    assert report.context_use_authorized is False
    assert report.deletion_authorized is False
    assert report.erasure_completed is False


@pytest.mark.parametrize(
    ("other_owner", "other_namespace"),
    (
        ("other-owner", "private"),
        ("owner", "notes"),
        ("other-owner", "notes"),
    ),
)
def test_revoked_private_scope_stays_isolated_from_unrelated_writes(
    tmp_path, other_owner, other_namespace,
):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    foreign = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    private = MemoryScope("owner", "private")
    unrelated = MemoryScope(other_owner, other_namespace)
    original = memory.put(
        MemoryWrite(private, "secret-source", "private content", expires_at_ms=150),
    )
    other = foreign.put(MemoryWrite(unrelated, "unrelated", "foreign content"))
    before = review_synthetic_retention_inventory(memory, private, ledger, now_ms=100)
    genesis = review_revocation_continuity(ledger)
    assert before.revoked is False
    assert len(before.items) == 1

    ledger.revoke(private, at_ms=101)
    after = review_synthetic_retention_inventory(
        memory, private, ledger, now_ms=100, retained_revocations=genesis,
    )
    unrelated_report = review_synthetic_retention_inventory(
        memory, unrelated, ledger, now_ms=100,
    )
    assert after.revoked is True
    assert unrelated_report.revoked is False
    assert after.inventory_digest != before.inventory_digest
    assert after.items == before.items
    assert after.items[0].memory_id == original.memory_id
    assert after.items[0].state is RetentionState.NOT_EXPIRED
    assert len(unrelated_report.items) == 1
    assert unrelated_report.items[0].memory_id == other.memory_id

    foreign.put(
        MemoryWrite(unrelated, "unrelated", "modified foreign content"),
        expected_revision=1,
    )
    again = review_synthetic_retention_inventory(
        memory, private, ledger, now_ms=100, retained_revocations=genesis,
    )
    assert again == after
    for report in (before, after, unrelated_report, again):
        _deny(report)
        assert "private content" not in repr(report)
        assert "foreign content" not in repr(report)


def test_expiry_purge_does_not_erase_independent_revocation_veto(tmp_path):
    path = tmp_path / "memory.sqlite"
    memory = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    purger = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    ledger_path = tmp_path / "revocations.sqlite"
    ledger = SyntheticContextRevocationLedger(ledger_path)
    scope = MemoryScope("owner", "private")
    memory.put(MemoryWrite(scope, "source", "sensitive text", expires_at_ms=150))
    ledger.revoke(scope, at_ms=110)
    retained = review_revocation_continuity(ledger)
    before = review_synthetic_retention_inventory(
        memory, scope, ledger, now_ms=100, retained_revocations=retained,
    )
    assert before.revoked is True
    assert before.items[0].state is RetentionState.NOT_EXPIRED
    assert purger.purge_expired(scope=scope) == 1
    after = review_synthetic_retention_inventory(
        SQLiteMemoryStore(path, clock_ms=lambda: 200),
        scope,
        SyntheticContextRevocationLedger(ledger_path),
        now_ms=200,
        retained_revocations=retained,
    )
    assert after.items == ()
    assert after.revoked is True
    assert after.inventory_digest != before.inventory_digest
    assert review_revocation_continuity(
        SyntheticContextRevocationLedger(ledger_path), retained=retained,
    ) == retained
    _deny(before)
    _deny(after)
    assert "sensitive text" not in repr(after)
