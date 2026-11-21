"""Synthetic observation identity binds private scope, source and parent lineage.

All payloads are in-memory fixtures; no media capture, real identity, consent,
network, device, notification or ToolBackend activity is permitted.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import make_disconnected_fixture
from ark.observations import ObservationKind

_PAYLOAD = b"synthetic confidential fixture - no real user content"
_PARENT = hashlib.sha256(b"synthetic parent fixture").hexdigest()


def _fixture(kind: ObservationKind, **changes: object):
    kwargs = {
        "kind": kind,
        "source_id": "local-fixture",
        "privacy_scope": "owner-one-private",
        "ingested_at_ms": 123,
        "payload": _PAYLOAD,
    }
    kwargs.update(changes)
    return make_disconnected_fixture(**kwargs)


@pytest.mark.parametrize("kind", tuple(ObservationKind))
@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("source_id", "different-local-fixture"),
        ("privacy_scope", "owner-two-private"),
    ),
)
def test_equal_private_bytes_cannot_alias_distinct_source_or_scope(
    kind: ObservationKind, field: str, replacement: str,
) -> None:
    first = _fixture(kind)
    second = _fixture(kind, **{field: replacement})
    expected_content = hashlib.sha256(_PAYLOAD).hexdigest()
    assert first.content_sha256 == second.content_sha256 == expected_content
    assert first.observation_id != second.observation_id
    assert first.adapter_id == second.adapter_id == "fixture.disconnected.v1"
    for envelope in (first, second):
        assert not hasattr(envelope, "payload")
        assert _PAYLOAD.decode("ascii") not in repr(envelope)


@pytest.mark.parametrize("kind", tuple(ObservationKind))
def test_parent_lineage_changes_identity_not_local_content_digest(
    kind: ObservationKind,
) -> None:
    unlinked = _fixture(kind)
    linked = _fixture(kind, parent_sha256=_PARENT)
    assert unlinked.parent_sha256 is None
    assert linked.parent_sha256 == _PARENT
    assert linked.content_sha256 == unlinked.content_sha256
    assert linked.observation_id != unlinked.observation_id
    assert linked.schema_version == unlinked.schema_version == 1


@pytest.mark.parametrize("kind", tuple(ObservationKind))
@pytest.mark.parametrize(
    "bad_parent",
    (
        "A" * 64,
        "0" * 63,
        "g" * 64,
        b"0" * 64,
    ),
)
def test_invalid_parent_digest_cannot_produce_private_fixture_envelope(
    kind: ObservationKind, bad_parent: object,
) -> None:
    with pytest.raises(ValueError) as error:
        _fixture(kind, parent_sha256=bad_parent)
    assert _PAYLOAD.decode("ascii") not in str(error.value)
