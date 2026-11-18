"""Run956: synthetic observation identity partitions metadata from payload.

No real image, microphone, screen, file, device or network data is obtained.
Matching content digests are not proof of identical provenance or consent.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import make_disconnected_fixture
from ark.observations import ObservationKind


_PRIVATE = b"PRIVATE_SYNTHETIC_FIXTURE_NO_EXTERNAL_CAPTURE"
_KINDS = tuple(ObservationKind)


def _make(kind: ObservationKind, **overrides: object):
    fields = {
        "kind": kind,
        "source_id": "fixture-source",
        "privacy_scope": "private:fixture",
        "ingested_at_ms": 100,
        "payload": _PRIVATE,
        "parent_sha256": None,
    }
    fields.update(overrides)
    return make_disconnected_fixture(**fields)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize(
    "changed",
    (
        "kind", "source_id", "privacy_scope", "ingested_at_ms",
        "parent_sha256",
    ),
)
def test_metadata_bound_observation_id_isolated_even_for_equal_payload(
    kind: ObservationKind, changed: str,
) -> None:
    original = _make(kind)
    changed_values = {
        "kind": _KINDS[(_KINDS.index(kind) + 1) % len(_KINDS)],
        "source_id": "fixture-other-source",
        "privacy_scope": "other:fixture",
        "ingested_at_ms": 101,
        "parent_sha256": "a" * 64,
    }
    altered = _make(kind, **{changed: changed_values[changed]})
    digest = hashlib.sha256(_PRIVATE).hexdigest()
    assert original.content_sha256 == altered.content_sha256 == digest
    assert original.observation_id != altered.observation_id
    assert original.adapter_id == altered.adapter_id == "fixture.disconnected.v1"
    assert _PRIVATE.decode("ascii") not in repr(original)
    assert _PRIVATE.decode("ascii") not in repr(altered)
    assert not hasattr(original, "payload")
    assert not hasattr(altered, "payload")


@pytest.mark.parametrize("kind", _KINDS)
def test_different_bytes_same_metadata_change_only_content_identity(
    kind: ObservationKind,
) -> None:
    first = _make(kind)
    second = _make(kind, payload=_PRIVATE + b"-second")
    assert first.kind is second.kind is kind
    assert first.source_id == second.source_id
    assert first.privacy_scope == second.privacy_scope
    assert first.content_sha256 != second.content_sha256
    assert first.observation_id != second.observation_id
    assert _PRIVATE.decode("ascii") not in repr(first)
    assert _PRIVATE.decode("ascii") not in repr(second)
