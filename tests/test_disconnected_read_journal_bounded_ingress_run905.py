"""Run905: synthetic READ journal retains exact bounded witness identities.

Only disconnected local receipt values are inspected: no SQLite file, backend,
real tool, external evidence, or user data is accessed.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_read_journal as mod

REQ = "req_" + "a" * 32
STEP = "step_" + "b" * 16
SHA = "c" * 64


def _receipt(*, request: str = REQ, step: str = STEP,
             input_digest: str = SHA, result_digest: str = SHA):
    return mod.ReadReceipt(request, step, "math.sum", input_digest, result_digest)


class _NoRegex:
    def fullmatch(self, _text):
        raise AssertionError("oversized field reached regex")


class _BoundedSHA:
    def __init__(self):
        self.original = re.compile(r"[0-9a-f]{64}\Z")
        self.seen: list[int] = []

    def fullmatch(self, text):
        if len(text) != 64:
            raise AssertionError("oversized SHA reached regex")
        self.seen.append(len(text))
        return self.original.fullmatch(text)


def test_valid_synthetic_receipt_and_genesis_are_non_authorizing():
    mod._check_receipt(_receipt())
    witness = mod.genesis_witness()
    mod._check_witness(witness)
    assert witness.dispatch_authorized is False
    assert witness.effect_proven is False
    assert witness.replay_authorized is False
    assert witness.independent_custody_proven is False


def test_oversized_witness_tip_refused_before_digest_regex(monkeypatch):
    monkeypatch.setattr(mod, "_SHA", _NoRegex())
    with pytest.raises(mod.ReadJournalRejected, match="witness"):
        mod._check_witness(mod.ReadJournalWitness(0, "f" * 200_000))


def test_oversized_request_refused_before_regex(monkeypatch):
    monkeypatch.setattr(mod, "_REQUEST", _NoRegex())
    with pytest.raises(mod.ReadJournalRejected, match="receipt"):
        mod._check_receipt(_receipt(request="req_" + "a" * 200_000))


def test_oversized_step_refused_before_regex(monkeypatch):
    monkeypatch.setattr(mod, "_STEP", _NoRegex())
    with pytest.raises(mod.ReadJournalRejected, match="receipt"):
        mod._check_receipt(_receipt(step="step_" + "f" * 200_000))


@pytest.mark.parametrize("field", ["input_digest", "result_digest"])
def test_oversized_digest_refused_before_regex(monkeypatch, field):
    checked = _BoundedSHA()
    monkeypatch.setattr(mod, "_SHA", checked)
    huge = "c" * 200_000
    data = {field: huge}
    with pytest.raises(mod.ReadJournalRejected, match="receipt"):
        mod._check_receipt(_receipt(**data))
    assert len(checked.seen) <= 1


@pytest.mark.parametrize("bad", [True, -1, 129, 1.0])
def test_retained_witness_count_requires_exact_bounded_int(bad):
    with pytest.raises(mod.ReadJournalRejected, match="witness"):
        mod._check_witness(mod.ReadJournalWitness(bad, SHA))


def test_invalid_digest_grammar_still_rejected():
    with pytest.raises(mod.ReadJournalRejected, match="receipt"):
        mod._check_receipt(_receipt(input_digest="G" * 64))
    with pytest.raises(mod.ReadJournalRejected, match="witness"):
        mod._check_witness(mod.ReadJournalWitness(0, "G" * 64))
