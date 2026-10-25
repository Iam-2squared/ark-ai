"""Read-only occurrence evidence must stay fixed across COMMIT/close.

These local SQLite witnesses do not establish consent or external exactly-once.
"""

import pytest

import ark.agency.synthetic_occurrence_continuity_review as module
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore


def _fresh_equal(value):
    alternate = ("!" + value)[1:]
    assert alternate == value and alternate is not value
    return alternate


class ConnectionHook:
    def __init__(self, inner, phase, mutate):
        self.inner = inner
        self.phase = phase
        self.mutate = mutate

    def commit(self):
        self.inner.commit()
        if self.phase == "commit":
            self.mutate()

    def close(self):
        self.inner.close()
        if self.phase == "close":
            self.mutate()

    def __getattr__(self, name):
        return getattr(self.inner, name)


@pytest.mark.parametrize("phase", ("commit", "close"))
@pytest.mark.parametrize("target", ("current", "retained"))
def test_sqlite_final_callbacks_cannot_swap_witness_carriers(
    tmp_path, monkeypatch, phase, target,
):
    path = tmp_path / "occurrences.sqlite"
    SyntheticOccurrenceStore(path)
    old = module.read_synthetic_ledger_witness(path)
    original_connect = module.sqlite3.connect
    original_integrity = module.SyntheticLedgerWitness.assert_integrity
    current = []

    def observed_integrity(self):
        original_integrity(self)
        if self is not old:
            current.append(self)

    def retarget():
        witness = current[-1] if target == "current" else old
        object.__setattr__(
            witness, "digest", _fresh_equal(witness.digest),
        )

    def connection(*args, **kwargs):
        return ConnectionHook(
            original_connect(*args, **kwargs), phase, retarget,
        )

    monkeypatch.setattr(
        module.SyntheticLedgerWitness, "assert_integrity", observed_integrity,
    )
    monkeypatch.setattr(module.sqlite3, "connect", connection)
    with pytest.raises(module.SyntheticReplayRejected, match="witness|retained"):
        module.read_synthetic_ledger_witness(path, retained=old)
    assert current


def test_unchanged_readonly_occurrence_witness_remains_stable(tmp_path):
    path = tmp_path / "occurrences.sqlite"
    SyntheticOccurrenceStore(path)
    first = module.read_synthetic_ledger_witness(path)
    latest = module.read_synthetic_ledger_witness(path, retained=first)
    assert first == latest
    assert latest.row_hashes == ()
    assert latest.digest.startswith("synthetic_ledger_")
