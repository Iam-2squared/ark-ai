"""Synthetic trigger evidence is inert and must survive COMMIT and close."""

import pytest

import ark.proactive_synthetic_continuity_review as module
from ark.proactive_synthetic_review import SyntheticProactiveLedger


def _equal_distinct(value):
    alternate = ("!" + value)[1:]
    assert alternate == value and alternate is not value
    return alternate


class ConnectionHook:
    def __init__(self, connection, phase, mutate):
        self.connection = connection
        self.phase = phase
        self.mutate = mutate

    def commit(self):
        self.connection.commit()
        if self.phase == "commit":
            self.mutate()

    def close(self):
        self.connection.close()
        if self.phase == "close":
            self.mutate()

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize("phase", ("commit", "close"))
@pytest.mark.parametrize("target", ("retained", "current"))
def test_final_sqlite_callbacks_cannot_swap_trigger_witness(
    tmp_path, monkeypatch, phase, target,
):
    path = tmp_path / "triggers.sqlite"
    SyntheticProactiveLedger(path)
    retained = module.read_proactive_witness(
        SyntheticProactiveLedger(path),
    )
    ledger = SyntheticProactiveLedger(path)
    original_connect = module.sqlite3.connect
    original_integrity = module.SyntheticTriggerWitness.assert_integrity
    fresh = []

    def capture(self):
        original_integrity(self)
        if self is not retained:
            fresh.append(self)

    def mutator():
        witness = retained if target == "retained" else fresh[-1]
        object.__setattr__(
            witness, "digest", _equal_distinct(witness.digest),
        )

    def connect(*args, **kwargs):
        if args[0] == ":memory:":
            return original_connect(*args, **kwargs)
        return ConnectionHook(
            original_connect(*args, **kwargs), phase, mutator,
        )

    monkeypatch.setattr(
        module.SyntheticTriggerWitness, "assert_integrity", capture,
    )
    monkeypatch.setattr(module.sqlite3, "connect", connect)
    with pytest.raises(module.SyntheticTriggerRejected, match="witness|retained"):
        module.read_proactive_witness(ledger, retained=retained)
    assert fresh


def test_stable_readonly_proactive_witness_is_inert(tmp_path):
    path = tmp_path / "triggers.sqlite"
    ledger = SyntheticProactiveLedger(path)
    first = module.read_proactive_witness(ledger)
    latest = module.read_proactive_witness(ledger, retained=first)
    assert latest == first
    assert latest.row_hashes == ()
    assert latest.digest.startswith("synthetic_triggers_")
