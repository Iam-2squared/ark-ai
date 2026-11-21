"""Run501 disconnected Memory genesis/epoch witness custody review."""

from dataclasses import replace

import pytest

import ark.memory.disconnected_witness_ledger as ledger
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview


def epoch():
    return AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
    )


def created(tmp_path):
    path = tmp_path / "ledger.sqlite"
    store = ledger.DisconnectedMemoryWitnessLedger(path, create=True)
    first = store.append(epoch(), retained=ledger.genesis_memory_ledger_witness())
    return store, first


def test_genesis_and_one_epoch_still_inspect_with_no_authority(tmp_path):
    store, first = created(tmp_path)
    genesis = ledger.genesis_memory_ledger_witness()
    assert genesis.epochs == 0
    assert len(genesis.chain_sha256) == 64
    assert store.inspect(retained=first) == first
    for value in (genesis, first):
        assert value.custody_authenticated is False
        assert value.independent_writer_proven is False
        assert value.historical_prefix_proven is False
        assert value.memory_disclosure_authorized is False
        assert value.dispatch_authorized is False


def test_genesis_constructor_cannot_forge_exact_type_fields(monkeypatch):
    saved = ledger.MemoryLedgerWitness

    def forged(*args):
        return replace(saved(*args), chain_sha256="f" * 64)

    monkeypatch.setattr(ledger, "MemoryLedgerWitness", forged)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="genesis"):
        ledger.genesis_memory_ledger_witness()


def test_genesis_constructor_cannot_forge_epoch(monkeypatch):
    saved = ledger.MemoryLedgerWitness

    def forged(*args):
        return replace(saved(*args), epochs=1)

    monkeypatch.setattr(ledger, "MemoryLedgerWitness", forged)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="genesis"):
        ledger.genesis_memory_ledger_witness()


def test_genesis_rejects_subclass_constructor(monkeypatch):
    saved = ledger.MemoryLedgerWitness

    class Forged(saved):
        pass

    monkeypatch.setattr(ledger, "MemoryLedgerWitness", Forged)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="retained witness"):
        ledger.genesis_memory_ledger_witness()


@pytest.mark.parametrize("flag", [
    "custody_authenticated", "independent_writer_proven",
    "historical_prefix_proven", "memory_disclosure_authorized",
    "dispatch_authorized",
])
def test_genesis_cannot_gain_claimed_authority(monkeypatch, flag):
    monkeypatch.setattr(
        ledger.MemoryLedgerWitness, flag, property(lambda self: True),
    )
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="authority"):
        ledger.genesis_memory_ledger_witness()


@pytest.mark.parametrize("mutation", ["epoch", "chain", "subclass"])
def test_read_history_cannot_be_rewritten_through_witness_factory(
    tmp_path, monkeypatch, mutation,
):
    store, first = created(tmp_path)
    saved = ledger.MemoryLedgerWitness

    class Forged(saved):
        pass

    def altered(epoch_number, digest):
        original = saved(epoch_number, digest)
        if epoch_number != 1:
            return original
        if mutation == "epoch":
            return replace(original, epochs=2)
        if mutation == "chain":
            return replace(original, chain_sha256="f" * 64)
        return Forged(epoch_number, digest)

    monkeypatch.setattr(ledger, "MemoryLedgerWitness", altered)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected):
        store.inspect(retained=first)
