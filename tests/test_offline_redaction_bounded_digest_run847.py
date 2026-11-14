"""Redaction digest/label width admission; no personal data or export."""

from __future__ import annotations

import hashlib

import pytest

from ark.offline_context_redaction import (
    OfflineRedactionRejected,
    OfflineRedactionSpan,
    preview_offline_redaction,
)

_DIGEST = "a" * 64
_TEXT = "synthetic"


def _preview(**overrides: object):
    arguments = {
        "owner_digest": _DIGEST,
        "scope_digest": _DIGEST,
        "retained_source_sha256": hashlib.sha256(_TEXT.encode()).hexdigest(),
        "spans": (OfflineRedactionSpan(0, len(_TEXT), "SYNTHETIC"),),
    }
    arguments.update(overrides)
    return preview_offline_redaction(_TEXT, **arguments)


@pytest.mark.parametrize("field", (
    "owner_digest", "scope_digest", "retained_source_sha256",
))
@pytest.mark.parametrize("size", (63, 65, 65_536))
def test_digest_exact_width_before_regex(field: str, size: int) -> None:
    with pytest.raises(OfflineRedactionRejected):
        _preview(**{field: "a" * size})


@pytest.mark.parametrize("size", (21, 65_536))
def test_untrusted_span_label_is_bounded_before_regex(size: int) -> None:
    with pytest.raises(OfflineRedactionRejected):
        _preview(spans=(OfflineRedactionSpan(0, len(_TEXT), "A" * size),))


def test_upper_accepted_label_boundary_remains_non_authorizing() -> None:
    result = _preview(spans=(OfflineRedactionSpan(0, len(_TEXT), "A" * 20),))
    assert result.masked_text == "[MASK:" + "A" * 20 + "]"
    assert result.complete_masking is True
    assert result.external_export_authorized is False
    assert result.consent_verified is False
    assert result.tool_dispatch_authorized is False
