"""Run747: synthetic clock digest callbacks are not a trusted-time source."""

import pytest

from ark.agency import synthetic_clock_sequence_review as clock


def _sample():
    return clock.SyntheticClockSample(1, "a" * 64, 1_000, 5_000)


def test_clock_digest_helper_replacement_refused_before_iterator_access(monkeypatch):
    invoked = []

    def hostile(*_args, **_kwargs):
        invoked.append("digest")
        raise AssertionError("unreviewed digest callback was executed")

    class PrivateSamples:
        def __iter__(self):
            invoked.append("iterator")
            raise AssertionError("clock samples were exposed")

    monkeypatch.setattr(clock, "_hash", hostile)
    with pytest.raises(clock.SyntheticClockRejected, match="digest implementation changed"):
        clock.review_synthetic_clock_sequence(PrivateSamples())
    assert invoked == []


@pytest.mark.parametrize("stage", ["iter", "next"])
def test_clock_digest_helper_rebinding_by_iterator_is_refused(monkeypatch, stage):
    invoked = []

    def hostile(*_args, **_kwargs):
        invoked.append("digest")
        raise AssertionError("substituted digest executed")

    class Samples:
        def __iter__(self):
            if stage == "iter":
                monkeypatch.setattr(clock, "_hash", hostile)
                return iter((_sample(),))

            def generate():
                monkeypatch.setattr(clock, "_hash", hostile)
                yield _sample()

            return generate()

    with pytest.raises(clock.SyntheticClockRejected, match="digest implementation changed"):
        clock.review_synthetic_clock_sequence(Samples())
    assert invoked == []


def test_original_clock_digest_helper_still_emits_non_authorizing_witness():
    witness = clock.review_synthetic_clock_sequence((_sample(),))
    assert witness.event_count == 1
    assert witness.source_digest == "a" * 64
    assert witness.chain_hash.startswith("clk_")
    assert witness.trusted_clock_verified is False
    assert witness.dispatch_authorized is False
    assert witness.automatic_replay_authorized is False
