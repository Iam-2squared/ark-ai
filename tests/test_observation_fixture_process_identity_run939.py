"""Observation fixture identity is reproducible without retaining private bytes.

Independent local Python processes re-create synthetic fixture digests only.
This does not authenticate capture provenance, consent or any live device.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ark.disconnected_observation_fixture import make_disconnected_fixture
from ark.observations import ObservationKind

_PAYLOAD = b"disconnected-synthetic-observation-fixture\x00"
_CHILD = r"""
import json
import sys

from ark.disconnected_observation_fixture import make_disconnected_fixture
from ark.observations import ObservationKind

item = make_disconnected_fixture(
    kind=ObservationKind(sys.argv[1]),
    source_id="synthetic-source",
    privacy_scope="synthetic-private",
    ingested_at_ms=123456,
    payload=b"disconnected-synthetic-observation-fixture\x00",
    parent_sha256=sys.argv[2] if sys.argv[2] != "-" else None,
)
print(json.dumps({
    "id": item.observation_id,
    "sha": item.content_sha256,
    "schema": item.schema_version,
    "adapter": item.adapter_id,
}))
"""


@pytest.mark.parametrize("kind", tuple(ObservationKind))
@pytest.mark.parametrize("parent", (None, "a" * 64))
def test_observation_fixture_identity_survives_independent_process_rebuild(
    kind: ObservationKind, parent: str | None,
) -> None:
    fixture = make_disconnected_fixture(
        kind=kind,
        source_id="synthetic-source",
        privacy_scope="synthetic-private",
        ingested_at_ms=123456,
        payload=_PAYLOAD,
        parent_sha256=parent,
    )
    result = subprocess.run(
        [sys.executable, "-c", _CHILD, kind.value, parent or "-"],
        capture_output=True, text=True, timeout=30, check=True,
    )
    recovered = json.loads(result.stdout)
    assert recovered == {
        "id": fixture.observation_id,
        "sha": fixture.content_sha256,
        "schema": 1,
        "adapter": "fixture.disconnected.v1",
    }
    assert _PAYLOAD.decode("utf-8") not in result.stdout
    assert _PAYLOAD.decode("utf-8") not in repr(fixture)
    assert not hasattr(fixture, "payload")

    # A scope change never merges two local observations even though raw
    # fixture bytes and opaque content SHA-256 remain exactly the same.
    foreign = make_disconnected_fixture(
        kind=kind,
        source_id="synthetic-source",
        privacy_scope="synthetic-other",
        ingested_at_ms=123456,
        payload=_PAYLOAD,
        parent_sha256=parent,
    )
    assert foreign.content_sha256 == fixture.content_sha256
    assert foreign.observation_id != fixture.observation_id
