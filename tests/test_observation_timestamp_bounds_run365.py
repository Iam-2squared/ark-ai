"""Offline observation identity timestamps share the durable SQLite integer domain."""

import re

import pytest

from ark.observations import ObservationEnvelope, ObservationKind

_MAX = 2**63 - 1


def _envelope(timestamp):
    return ObservationEnvelope(
        ObservationKind.TEXT, "offline-source", "fixture-adapter",
        "fixture:private", timestamp, "a" * 64,
    )


@pytest.mark.parametrize("invalid", (-1, True, 1.25, 2**63, 2**100))
def test_observation_rejects_out_of_domain_ingestion_time(invalid):
    with pytest.raises(ValueError, match="non-negative exact integer"):
        _envelope(invalid)


def test_observation_accepts_sqlite_limit_and_stable_identity():
    envelope = _envelope(_MAX)
    assert envelope.ingested_at_ms == _MAX
    assert re.fullmatch(r"obs_[0-9a-f]{64}", envelope.observation_id)
    assert _envelope(_MAX).observation_id == envelope.observation_id
    assert _envelope(_MAX - 1).observation_id != envelope.observation_id


def test_existing_small_timestamp_identity_is_unchanged():
    envelope = ObservationEnvelope(
        ObservationKind.TRANSCRIPT, "s", "a", "p", 1, "a" * 64, "b" * 64,
    )
    assert envelope.observation_id == (
        "obs_e2e66d490467566c58307581de449f278a2bf9755685af1343d66c458513b3d0"
    )
