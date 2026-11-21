"""Private preview parsing must remain original before private content is touched."""

from __future__ import annotations

import hashlib

import pytest

import ark.personal_context_preview_delta as delta
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64
_RETAINED = "c" * 64


@pytest.mark.parametrize(
    "replacement",
    ("parse", "duplicate_keys", "source_guard", "hashlib_module", "json_module"),
)
def test_substituted_private_parser_rejected_before_untrusted_callback(
    monkeypatch: pytest.MonkeyPatch, replacement: str,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("substituted parser or guard was invoked")

    with monkeypatch.context() as patch:
        if replacement == "parse":
            patch.setattr(delta, "_parse", forbidden)
        elif replacement == "duplicate_keys":
            patch.setattr(delta, "_duplicate_refusal", forbidden)
        elif replacement == "source_guard":
            patch.setattr(delta, "_assert_original_preview_denials", forbidden)
        elif replacement == "hashlib_module":
            patch.setattr(delta, "hashlib", object())
        else:
            patch.setattr(delta, "json", object())

        with pytest.raises(delta.PrivateContextDeltaRejected, match="protocol"):
            delta.review_private_context_delta(
                None, None,
                owner_digest=_OWNER,
                allowed_scope_digests=(_SCOPE,),
                independently_retained_prior_digest=_RETAINED,
            )


def test_original_private_parser_still_reports_content_free_change_counts() -> None:
    old_content = "private-old"
    new_content = "private-new"

    def preview(text: str):
        fixture = OfflineContextFixture(
            record_id="rec_" + "1" * 32,
            owner_digest=_OWNER,
            scope_digest=_SCOPE,
            content=text,
            content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            expires_at_ms=1000,
        )
        return build_offline_context_preview(
            (fixture,),
            owner_digest=_OWNER,
            allowed_scope_digests=(_SCOPE,),
            observed_at_ms=50,
        )

    prior, current = preview(old_content), preview(new_content)
    result = delta.review_private_context_delta(
        prior, current,
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        independently_retained_prior_digest=prior.local_digest,
    )
    assert result.change_state == "REVIEW_REQUIRED"
    assert (result.added_count, result.removed_count,
            result.changed_count, result.retained_count) == (0, 0, 1, 0)
    assert result.reuse_authorized is False
    assert result.deletion_authorized is False
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert old_content not in repr(result)
    assert new_content not in repr(result)
