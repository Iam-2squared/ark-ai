"""Synthetic atomic preaction codec/DDL/capacity custody and rollback.

Only disposable ledger files and fabricated request digests are involved.
Inert intent/audit equality is not approval, exactly-once real execution,
independently authenticated evidence, or permission to replay.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic


@pytest.mark.parametrize("mutation", (
    "hashlib", "json", "_DOMAIN", "_AUDIT_DOMAIN", "_GENESIS",
    "_INTENTS", "_AUDITS", "_MAX", "_MAX_BOOL", "_MAX_TEXT",
))
def test_codec_or_schema_tamper_rejected_before_db_creation(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    target = tmp_path / "never-create.sqlite"
    values = {
        "hashlib": object(),
        "json": object(),
        "_DOMAIN": b"replaced-chain-domain",
        "_AUDIT_DOMAIN": b"replaced-audit-domain",
        "_GENESIS": "0" * 64,
        "_INTENTS": "CREATE TABLE swapped(x)",
        "_AUDITS": "CREATE TABLE swapped(y)",
        "_MAX": 999,
        "_MAX_BOOL": True,
        "_MAX_TEXT": "128",
    }
    key = "_MAX" if mutation.startswith("_MAX") else mutation
    with monkeypatch.context() as patch:
        patch.setattr(atomic, key, values[mutation])
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="codec or schema changed",
        ):
            atomic.DisconnectedAtomicPreactionLedger.create(target)
    assert not target.exists()


def test_digest_dependency_mutation_cannot_run_synthetic_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(atomic, "json", object())
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="codec or schema changed",
        ):
            atomic._digest(b"offline", ("synthetic",))


def test_local_audit_epoch_rolls_back_on_digest_callback_drift(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(
        tmp_path / "local-inert-ledger.sqlite",
    )
    retained = atomic.genesis_atomic_preaction_witness()
    claim = atomic.AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)
    original = atomic._digest

    with monkeypatch.context() as patch:
        def retarget(domain: bytes, row: tuple[object, ...]) -> str:
            observed = original(domain, row)
            patch.setattr(atomic, "_AUDIT_DOMAIN", b"changed-at-callback")
            return observed

        patch.setattr(atomic, "_digest", retarget)
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="codec or schema changed",
        ):
            ledger.reserve(claim, retained=retained)
    snapshot = ledger.inspect(retained)
    assert snapshot.witness.count == 0
    assert snapshot.occurrence_ids == ()
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False


def test_valid_synthetic_claim_audit_remains_local_and_denial_only(tmp_path) -> None:
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(
        tmp_path / "local-valid-ledger.sqlite",
    )
    before = atomic.genesis_atomic_preaction_witness()
    claim = atomic.AtomicIntentClaim("occ_" + "d" * 64, "bound_" + "e" * 64, "f" * 64)
    after = ledger.reserve(claim, retained=before)
    observed = ledger.inspect(after)
    assert after.count == 1
    assert observed.occurrence_ids == (claim.occurrence_id,)
    assert observed.tool_dispatch_authorized is False
    assert observed.automatic_replay_authorized is False
    assert observed.trusted_approval_verified is False
    assert observed.independent_custody_proven is False
