"""A reflected-mutable exported empty clock witness is not trusted genesis."""

import hashlib

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def _sample():
    return clock.SyntheticClockSample(
        1, hashlib.sha256(b"local").hexdigest(), 100, 1000,
    )


@pytest.mark.parametrize("tamper", ("replace", "reflective"))
def test_poisoned_exported_empty_witness_cannot_reseed_replay(monkeypatch, tamper):
    first = clock.review_synthetic_clock_sequence((_sample(),))
    if tamper == "replace":
        monkeypatch.setattr(
            clock, "EMPTY_CLOCK_WITNESS",
            clock.SyntheticClockWitness(0, "", -1, -1, "clk_" + "f" * 64),
        )
    else:
        clean = clock.SyntheticClockWitness(*clock._EMPTY_FIELDS)
        monkeypatch.setattr(clock, "EMPTY_CLOCK_WITNESS", clean)
        object.__setattr__(clean, "chain_hash", "clk_" + "f" * 64)
    subsequent = clock.review_synthetic_clock_sequence((_sample(),))
    assert subsequent == first
    assert subsequent.chain_hash == first.chain_hash
    assert not subsequent.trusted_clock_verified
    assert not subsequent.dispatch_authorized


def test_poisoned_empty_witness_does_not_redefine_validation(monkeypatch):
    bogus = clock.SyntheticClockWitness(0, "", -1, -1, "clk_" + "f" * 64)
    monkeypatch.setattr(clock, "EMPTY_CLOCK_WITNESS", bogus)
    with pytest.raises(clock.SyntheticClockRejected, match="invalid synthetic clock witness"):
        clock.review_synthetic_clock_sequence((_sample(),), retained=bogus)


def test_unmodified_empty_witness_preserves_valid_prefix():
    witness = clock.review_synthetic_clock_sequence((_sample(),))
    from_genesis = clock.review_synthetic_clock_sequence(
        (_sample(),), retained=clock.EMPTY_CLOCK_WITNESS,
    )
    assert from_genesis == witness
    assert from_genesis.automatic_replay_authorized is False
