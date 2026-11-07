"""Privacy veto history checks each phase without authorizing Context reuse."""

from pathlib import Path

import pytest

import ark.personal_context_revocation_continuity_review as module
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _store(tmp_path: Path):
    return SyntheticContextRevocationLedger(tmp_path / "revocation epoch # %.sqlite")


def test_source_swap_during_schema_read_is_not_hidden_by_hash(
    tmp_path: Path, monkeypatch,
):
    ledger = _store(tmp_path)
    original_path = ledger.path
    validate = module._validate
    digest = module._hash
    changed = False
    restored = False

    def inject_validate(conn):
        nonlocal changed
        validate(conn)
        ledger.path = Path(str(original_path))
        changed = True

    def inject_hash(rows):
        nonlocal restored
        if changed:
            ledger.path = original_path
            restored = True
        return digest(rows)

    monkeypatch.setattr(module, "_validate", inject_validate)
    monkeypatch.setattr(module, "_hash", inject_hash)
    with pytest.raises(SyntheticContextRevocationRejected, match="source path"):
        module.review_revocation_continuity(ledger)
    assert changed and not restored


@pytest.mark.parametrize("field", ("rows", "witness_id"))
def test_retained_witness_schema_phase_mutation_cannot_be_restored(
    tmp_path: Path, monkeypatch, field: str,
):
    ledger = _store(tmp_path)
    ledger.revoke(MemoryScope("offline", "synthetic"), at_ms=10)
    retained = module.review_revocation_continuity(ledger)
    original = getattr(retained, field)
    validate = module._validate
    digest = module._hash
    changed = False
    restored = False

    def inject_validate(conn):
        nonlocal changed
        validate(conn)
        if field == "rows":
            object.__setattr__(retained, field, ())
        else:
            object.__setattr__(retained, field, "rvk_" + "0" * 64)
        changed = True

    def inject_hash(rows):
        nonlocal restored
        if changed:
            restored = True
            object.__setattr__(retained, field, original)
        return digest(rows)

    monkeypatch.setattr(module, "_validate", inject_validate)
    monkeypatch.setattr(module, "_hash", inject_hash)
    with pytest.raises(SyntheticContextRevocationRejected, match="retained"):
        module.review_revocation_continuity(ledger, retained=retained)
    assert changed and not restored


def test_path_mutation_after_hash_cannot_be_restored_by_witness_integrity(
    tmp_path: Path, monkeypatch,
):
    ledger = _store(tmp_path)
    original_path = ledger.path
    digest = module._hash
    calls = 0

    def inject(rows):
        nonlocal calls
        result = digest(rows)
        calls += 1
        if calls == 1:
            ledger.path = Path(str(original_path))
        else:
            ledger.path = original_path
        return result

    monkeypatch.setattr(module, "_hash", inject)
    with pytest.raises(SyntheticContextRevocationRejected, match="source path"):
        module.review_revocation_continuity(ledger)
    assert calls == 1


def test_retained_mutation_after_hash_detected_before_second_hash(
    tmp_path: Path, monkeypatch,
):
    ledger = _store(tmp_path)
    ledger.revoke(MemoryScope("offline", "synthetic"), at_ms=10)
    retained = module.review_revocation_continuity(ledger)
    original_id = retained.witness_id
    digest = module._hash
    validate = module._validate
    in_read = False
    calls = 0

    def mark_validation(conn):
        nonlocal in_read
        validate(conn)
        in_read = True

    def inject(rows):
        nonlocal calls
        result = digest(rows)
        if in_read:
            calls += 1
            object.__setattr__(
                retained, "witness_id",
                "rvk_" + "0" * 64 if calls == 1 else original_id,
            )
        return result

    monkeypatch.setattr(module, "_validate", mark_validation)
    monkeypatch.setattr(module, "_hash", inject)
    with pytest.raises(SyntheticContextRevocationRejected, match="retained"):
        module.review_revocation_continuity(ledger, retained=retained)
    assert calls == 1


def test_stable_history_remains_deny_only_with_independent_prefix(tmp_path: Path):
    ledger = _store(tmp_path)
    genesis = module.review_revocation_continuity(ledger)
    ledger.revoke(MemoryScope("offline", "synthetic"), at_ms=10)
    latest = module.review_revocation_continuity(ledger, retained=genesis)
    assert latest != genesis
    assert len(latest.rows) == 1
    assert module.review_revocation_continuity(ledger, retained=latest) == latest
