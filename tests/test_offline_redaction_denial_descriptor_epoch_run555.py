"""A local masking preview must not accept reentrant authority descriptors.

Synthetic source bytes remain local and fully masked. No real permission,
consent, erasure, notification or export follows from a clean fixture.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_redaction as redaction


def _preview():
    source = "synthetic-private-data"
    return redaction.preview_offline_redaction(
        source,
        owner_digest="a" * 64,
        scope_digest="b" * 64,
        retained_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, len(source), "SECRET"),),
    )


@pytest.mark.parametrize("replaced", (
    "consent_verified", "privacy_erasure_proven",
    "external_export_authorized",
))
def test_last_false_denial_cannot_replace_earlier_authority_getter(
    monkeypatch, replaced,
):
    with monkeypatch.context() as patch:
        def malicious(self):
            # A False-only replacement can still have arbitrary side effects.
            # The earlier getter has already been read by this point.
            patch.setattr(
                redaction.RedactedOfflinePreview, replaced,
                property(lambda _result: False),
            )
            return False

        patch.setattr(
            redaction.RedactedOfflinePreview, "tool_dispatch_authorized",
            property(malicious),
        )
        with pytest.raises(
            redaction.OfflineRedactionRejected, match="authority definition changed",
        ):
            _preview()


def test_intact_full_mask_stays_local_and_non_authorizing():
    result = _preview()
    assert result.masked_text == "[MASK:SECRET]"
    assert result.complete_masking is True
    assert result.masked_characters == len("synthetic-private-data")
    assert all(
        getattr(result, flag) is False for flag in redaction._DENIAL_NAMES
    )
