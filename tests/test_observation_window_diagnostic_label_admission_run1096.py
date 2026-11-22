"""Run1096: optional observation windows reject spoofable diagnostic labels.

The frozen ObservationEnvelope v1 constructor remains unchanged. These checks
cover only the stricter offline review boundary; no media capture or dispatch.
"""

from __future__ import annotations

import pytest

from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(**overrides: str) -> ObservationEnvelope:
    values = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "adapter_id": "offline-fixture",
        "privacy_scope": "private",
        "ingested_at_ms": 95,
        "content_sha256": "a" * 64,
    }
    values.update(overrides)
    return ObservationEnvelope(**values)


@pytest.mark.parametrize(
    ("field", "raw", "message"),
    (
        ("source_id", "source\nid", "ASCII control"),
        ("adapter_id", "adapter\tid", "ASCII control"),
        ("privacy_scope", "private\nscope", "ASCII control"),
        ("source_id", "source\u0085id", "Unicode formatting control"),
        ("adapter_id", "adapter\u202e-id", "Unicode formatting control"),
        ("privacy_scope", "private\u200b-scope", "Unicode formatting control"),
        ("source_id", "source\x00id", "NUL"),
    ),
)
def test_optional_window_rejects_spoofable_labels_without_tightening_envelope_v1(
    field: str, raw: str, message: str,
) -> None:
    envelope = _envelope(**{field: raw})
    # The frozen envelope constructor is deliberately unchanged; the stricter
    # opt-in reviewer rejects before calculating any observation identity.
    assert getattr(envelope, field) == raw
    scope = raw if field == "privacy_scope" else "private"
    with pytest.raises(ValueError, match=message):
        ObservationWindowReview(scope, 100, 10, (envelope,))


def test_optional_window_keeps_ordinary_multilingual_labels() -> None:
    envelope = _envelope(
        source_id="source-記録",
        adapter_id="offline-テキスト",
        privacy_scope="private-個人",
    )
    review = ObservationWindowReview(
        "private-個人", 100, 10, (envelope,),
    )
    review.assert_fresh_at(100)
    assert review.envelopes == (envelope,)
