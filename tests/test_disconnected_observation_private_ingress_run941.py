"""Disconnected fixture privacy and exact-type admission before private access.

Only in-memory synthetic bytes. No camera, microphone, screen, network,
credential, permission, or live action is used or authorized.
"""

from __future__ import annotations

import pytest

from ark.disconnected_observation_fixture import (
    DisconnectedFixtureRejected,
    make_disconnected_fixture,
)
from ark.observations import ObservationKind

_PRIVATE = b"synthetic-private-payload-not-for-logging"


def _input(kind: ObservationKind) -> dict[str, object]:
    return {
        "kind": kind,
        "source_id": "synthetic-source",
        "privacy_scope": "synthetic-private",
        "ingested_at_ms": 123,
        "payload": _PRIVATE,
    }


@pytest.mark.parametrize("kind", tuple(ObservationKind))
@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("source_id", "synthetic\x00hidden"),
        ("privacy_scope", "\ud800"),
        ("ingested_at_ms", True),
    ),
)
def test_invalid_metadata_never_returns_or_echoes_private_fixture(
    kind: ObservationKind, field: str, invalid: object,
) -> None:
    arguments = _input(kind)
    arguments[field] = invalid
    with pytest.raises(ValueError) as error:
        make_disconnected_fixture(**arguments)
    assert _PRIVATE.decode("ascii") not in str(error.value)


class _DeceptivePayload:
    def __init__(self) -> None:
        self.hooks_called = 0

    def __len__(self) -> int:
        self.hooks_called += 1
        raise AssertionError("payload length hook must not run")

    def __bytes__(self) -> bytes:
        self.hooks_called += 1
        raise AssertionError("payload conversion hook must not run")


@pytest.mark.parametrize("kind", tuple(ObservationKind))
def test_deceptive_private_buffer_refused_without_running_python_hooks(
    kind: ObservationKind,
) -> None:
    payload = _DeceptivePayload()
    arguments = _input(kind)
    arguments["payload"] = payload
    with pytest.raises(DisconnectedFixtureRejected, match="exact bytes"):
        make_disconnected_fixture(**arguments)
    assert payload.hooks_called == 0
