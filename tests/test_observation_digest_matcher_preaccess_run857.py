"""Bound observation digest ingress and refuse substituted regex callbacks.

Only synthetic labels are used. No source attestation, sensor access,
private-media disclosure or real-world actions are enabled.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark import observations
from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(*, content: object = "a" * 64, parent: object = None) -> ObservationEnvelope:
    return ObservationEnvelope(
        kind=ObservationKind.TEXT,
        source_id="synthetic-source",
        adapter_id="disconnected-fixture",
        privacy_scope="local-only",
        ingested_at_ms=1,
        content_sha256=content,
        parent_sha256=parent,
    )


@pytest.mark.parametrize(
    ("field", "digest"),
    (
        ("content", "b" * 65),
        ("content", "c" * 8192),
        ("content", b"a" * 64),
        ("parent", "d" * 8192),
    ),
)
def test_noncanonical_digest_shape_denied(field: str, digest: object) -> None:
    options = {"content": digest} if field == "content" else {"parent": digest}
    with pytest.raises(ValueError, match="exact lowercase SHA-256"):
        _envelope(**options)


def test_substituted_matcher_refused_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def untrusted_matcher(*args: object) -> object:
        calls.append(args)
        raise AssertionError("foreign regex callback received observation digest")

    with monkeypatch.context() as patch:
        patch.setattr(
            observations, "re", SimpleNamespace(fullmatch=untrusted_matcher),
        )
        with pytest.raises(ValueError, match="observation digest matcher changed"):
            _envelope()
    assert calls == []


def test_valid_synthetic_observation_identity_remains_deterministic() -> None:
    item = _envelope(parent="b" * 64)
    assert item.observation_id == item.observation_id
    assert item.observation_id.startswith("obs_")
