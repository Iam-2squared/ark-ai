"""Retained revocation witness IDs must remain exact original carriers.

These are disposable local privacy reviews only: no consent, erasure,
notification, disclosure, external execution or authenticated clock.
"""

import pytest

import ark.personal_context_retention_recheck_review as recheck
import ark.personal_context_revocation_continuity_review as continuity
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _clone(value):
    changed = ("!" + value)[1:]
    assert changed == value and changed is not value
    return changed


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("local-user", "private")
    memory.put(MemoryWrite(
        scope, "local-fixture", "PRIVATE TEST RECORD", expires_at_ms=101,
    ))
    revocations = SyntheticContextRevocationLedger(tmp_path / "revoked.sqlite")
    retained = continuity.review_revocation_continuity(revocations)
    inventory = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
        retained_revocations=retained,
    )
    return memory, scope, revocations, inventory, retained


@pytest.mark.parametrize("callback", ("integrity", "schema"))
def test_continuity_rejects_equal_witness_id_replacement(
    tmp_path, monkeypatch, callback,
):
    _memory, _scope, revocations, _inventory, retained = _fixture(tmp_path)
    injections = []

    if callback == "integrity":
        native = continuity.SyntheticRevocationWitness.assert_integrity

        def mutate_after_integrity(self):
            result = native(self)
            if self is retained and not injections:
                object.__setattr__(retained, "witness_id", _clone(retained.witness_id))
                injections.append(True)
            return result

        monkeypatch.setattr(
            continuity.SyntheticRevocationWitness,
            "assert_integrity", mutate_after_integrity,
        )
    else:
        native = continuity._validate

        def mutate_after_schema(conn):
            result = native(conn)
            if not injections:
                object.__setattr__(retained, "witness_id", _clone(retained.witness_id))
                injections.append(True)
            return result

        monkeypatch.setattr(continuity, "_validate", mutate_after_schema)

    with pytest.raises(
        continuity.SyntheticContextRevocationRejected,
        match="retained revocation evidence changed",
    ):
        continuity.review_revocation_continuity(
            revocations, retained=retained,
        )
    assert injections == [True]


@pytest.mark.parametrize("phase", (1, 3))
def test_retention_recheck_rejects_equal_retained_witness_id(
    tmp_path, monkeypatch, phase,
):
    memory, scope, revocations, cached, retained = _fixture(tmp_path)
    native = recheck.review_synthetic_retention_inventory
    calls = []

    def inventory_with_retained_substitution(*args, **kwargs):
        result = native(*args, **kwargs)
        calls.append(True)
        if len(calls) == phase:
            object.__setattr__(retained, "witness_id", _clone(retained.witness_id))
        return result

    monkeypatch.setattr(
        recheck, "review_synthetic_retention_inventory",
        inventory_with_retained_substitution,
    )
    with pytest.raises(
        recheck.SyntheticRetentionRecheckRejected,
        match="retention source or evidence changed",
    ):
        recheck.review_synthetic_retention_recheck(
            memory, scope, revocations, cached, now_ms=101,
            max_age_ms=10, retained_revocations=retained,
        )
    assert len(calls) == phase


def test_unchanged_revocation_prefix_yields_deny_only_privacy_review(tmp_path):
    memory, scope, revocations, cached, retained = _fixture(tmp_path)
    latest = continuity.review_revocation_continuity(
        revocations, retained=retained,
    )
    assert latest == retained
    result = recheck.review_synthetic_retention_recheck(
        memory, scope, revocations, cached,
        now_ms=101, max_age_ms=10, retained_revocations=retained,
    )
    assert result.expired_memory_ids
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "PRIVATE TEST RECORD" not in repr(result)
