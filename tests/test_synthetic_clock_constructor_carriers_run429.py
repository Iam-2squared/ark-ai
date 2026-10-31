"""A forged clock-witness constructor must not substitute equal-text carriers.

Everything is caller-supplied synthetic time. A local hash chain does not
authenticate the source, confer consent, or enable external Tool execution.
"""

import hashlib

import pytest

import ark.agency.synthetic_clock_sequence_review as clock


def _distinct_equal(value):
    alternate = ("!" + value)[1:]
    assert alternate == value and alternate is not value
    return alternate


@pytest.mark.parametrize("field", ("source_digest", "chain_hash"))
def test_constructor_cannot_replace_original_clock_witness_carrier(
    monkeypatch, field,
):
    original_init = clock.SyntheticClockWitness.__init__
    constructed = []

    def substituted_init(
        self, event_count, source_digest, last_wall_ms,
        last_monotonic_ns, chain_hash,
    ):
        original_init(
            self, event_count, source_digest, last_wall_ms,
            last_monotonic_ns, chain_hash,
        )
        if event_count:
            constructed.append(event_count)
            object.__setattr__(
                self, field, _distinct_equal(getattr(self, field)),
            )

    monkeypatch.setattr(clock.SyntheticClockWitness, "__init__", substituted_init)
    sample = clock.SyntheticClockSample(
        1, hashlib.sha256(b"offline-source").hexdigest(), 17, 20,
    )
    with pytest.raises(
        clock.SyntheticClockRejected, match="constructed clock chain link changed",
    ):
        clock.review_synthetic_clock_sequence((sample,))
    assert constructed == [1]


def test_ordinary_constructed_clock_witness_keeps_original_sample_carrier():
    source = hashlib.sha256(b"offline-source").hexdigest()
    sample = clock.SyntheticClockSample(1, source, 17, 20)
    result = clock.review_synthetic_clock_sequence((sample,))
    assert result.source_digest is sample.source_digest
    assert result.event_count == 1
    assert result.last_wall_ms == 17
    assert result.last_monotonic_ns == 20
    assert result.trusted_clock_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
