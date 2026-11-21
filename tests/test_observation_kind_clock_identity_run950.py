"""Run950: disconnected Observation identity binds type and caller time.

All media bytes are synthetic in-memory fixtures; no camera, microphone,
screen, network, user-data read or external executor is involved.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import make_disconnected_fixture
from ark.observations import ObservationKind

_PRIVATE = b"synthetic private payload; do not disclose actual media"
_PARENT = hashlib.sha256(b"synthetic inert parent").hexdigest()


def _fixture(kind: ObservationKind, at_ms: int):
    return make_disconnected_fixture(
        kind=kind,
        source_id="local-fixture",
        privacy_scope="synthetic-owner-private",
        ingested_at_ms=at_ms,
        payload=_PRIVATE,
        parent_sha256=_PARENT,
    )


@pytest.mark.parametrize("kind", tuple(ObservationKind))
@pytest.mark.parametrize("other_clock", (1, 2**63 - 1))
def test_same_payload_and_parent_cannot_alias_distinct_observed_time(
    kind: ObservationKind, other_clock: int,
) -> None:
    first = _fixture(kind, 0)
    other = _fixture(kind, other_clock)
    assert first.content_sha256 == other.content_sha256
    assert first.content_sha256 == hashlib.sha256(_PRIVATE).hexdigest()
    assert first.parent_sha256 == other.parent_sha256 == _PARENT
    assert first.observation_id != other.observation_id
    assert len(first.observation_id) == len(other.observation_id) == 68
    assert _PRIVATE.decode("ascii") not in repr(first)
    assert _PRIVATE.decode("ascii") not in repr(other)
    assert not hasattr(first, "payload")
    assert not hasattr(other, "payload")


@pytest.mark.parametrize(("first_kind", "second_kind"), (
    (ObservationKind.TEXT, ObservationKind.TRANSCRIPT),
    (ObservationKind.TEXT, ObservationKind.IMAGE),
    (ObservationKind.IMAGE, ObservationKind.SCREEN),
    (ObservationKind.SCREEN, ObservationKind.TRANSCRIPT),
))
def test_equal_content_scope_clock_and_parent_are_kind_separated(
    first_kind: ObservationKind, second_kind: ObservationKind,
) -> None:
    first = _fixture(first_kind, 123)
    second = _fixture(second_kind, 123)
    assert first.kind is first_kind
    assert second.kind is second_kind
    assert first.content_sha256 == second.content_sha256
    assert first.parent_sha256 == second.parent_sha256
    assert first.observation_id != second.observation_id
    assert first.adapter_id == second.adapter_id == "fixture.disconnected.v1"
    assert first.schema_version == second.schema_version == 1
    assert _PRIVATE.decode("ascii") not in repr((first, second))
