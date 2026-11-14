"""Disconnected privacy window and rollover timestamps remain SQLite-safe."""

import hashlib

import pytest

from ark.observation_rollover_review import ObservationRolloverWitness
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind

_MAX = 2**63 - 1


def _envelope(timestamp):
    return ObservationEnvelope(
        ObservationKind.TEXT, "source", "offline", "private:fixture",
        timestamp, hashlib.sha256(b"fixture").hexdigest(),
    )


@pytest.mark.parametrize("bad", (-1, True, 2**63, 2**100))
def test_window_rejects_invalid_review_time(bad):
    with pytest.raises(ValueError, match="observed_at_ms"):
        ObservationWindowReview("private:fixture", bad, 0, (_envelope(0),))


@pytest.mark.parametrize("bad", (-1, False, 2**63, 2**100))
def test_window_rejects_invalid_age_budget(bad):
    with pytest.raises(ValueError, match="max_age_ms"):
        ObservationWindowReview("private:fixture", 0, bad, (_envelope(0),))


def test_window_accepts_valid_sqlite_timestamp_upper_boundary():
    window = ObservationWindowReview(
        "private:fixture", _MAX, 0, (_envelope(_MAX),)
    )
    window.assert_fresh_at(_MAX)
    assert window.witness.startswith("window_")


def test_window_accepts_maximum_valid_retention_duration():
    window = ObservationWindowReview(
        "private:fixture", _MAX, _MAX, (_envelope(0),)
    )
    window.assert_fresh_at(_MAX)


@pytest.mark.parametrize("bad", (-1, True, 2**63, 2**100))
def test_rollover_witness_rejects_out_of_range_time(bad):
    with pytest.raises(ValueError, match="rollover observation time"):
        ObservationRolloverWitness(
            "private:fixture", bad, "window_" + "0" * 64, 1, "a" * 64,
        )


def test_rollover_witness_accepts_bounded_time():
    witness = ObservationRolloverWitness(
        "private:fixture", _MAX, "window_" + "0" * 64, 1, "a" * 64,
    )
    assert witness.observed_at_ms == _MAX
