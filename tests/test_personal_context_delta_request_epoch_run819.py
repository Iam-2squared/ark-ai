"""Detached private-context deltas never turn request digests into consent."""

from __future__ import annotations

import hashlib

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_preview_delta import (
    PrivateContextDeltaRejected,
    review_private_context_delta,
)
from ark.personal_context_request_binding import bind_offline_context_request

_OWNER = "a" * 64
_SCOPES = ("b" * 64, "c" * 64)
_REQUEST = "ctxreq_" + "1" * 64


def _item(n, content, *, scope=_SCOPES[0]):
    return OfflineContextFixture(
        f"rec_{n:032x}", _OWNER, scope, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 1000,
    )


def _preview(*rows):
    return build_offline_context_preview(
        tuple(rows), owner_digest=_OWNER,
        allowed_scope_digests=_SCOPES, observed_at_ms=100,
    )


def _deny_binding(binding):
    assert binding.consent_verified is False
    assert binding.revocation_freshness_verified is False
    assert binding.external_export_authorized is False
    assert binding.tool_dispatch_authorized is False
    assert binding.retention_authorized is False


def _deny_delta(delta):
    assert delta.reuse_authorized is False
    assert delta.deletion_authorized is False
    assert delta.consent_verified is False
    assert delta.external_export_authorized is False


@pytest.mark.parametrize(
    "case,expected",
    (
        ("same", "UNCHANGED"),
        ("edit", "REVIEW_REQUIRED"),
        ("add", "REVIEW_REQUIRED"),
        ("remove", "REVIEW_REQUIRED"),
        ("scope-migrate", "REJECT"),
    ),
)
def test_private_delta_and_request_binding_are_never_consent_or_reuse(
    case, expected,
):
    before = _preview(_item(1, "secret-old"), _item(2, "shared"))
    changed = {
        "same": (_item(1, "secret-old"), _item(2, "shared")),
        "edit": (_item(1, "secret-new"), _item(2, "shared")),
        "add": (
            _item(1, "secret-old"), _item(2, "shared"), _item(3, "extra"),
        ),
        "remove": (_item(1, "secret-old"),),
        "scope-migrate": (
            _item(1, "secret-old", scope=_SCOPES[1]), _item(2, "shared"),
        ),
    }[case]
    after = _preview(*changed)

    old_binding = bind_offline_context_request(_REQUEST, before)
    new_binding = bind_offline_context_request(_REQUEST, after)
    _deny_binding(old_binding)
    _deny_binding(new_binding)
    assert old_binding.context_digest == before.local_digest
    assert new_binding.context_digest == after.local_digest

    if case == "same":
        assert old_binding.binding_digest == new_binding.binding_digest
    else:
        assert old_binding.binding_digest != new_binding.binding_digest

    kwargs = {
        "owner_digest": _OWNER,
        "allowed_scope_digests": _SCOPES,
        "independently_retained_prior_digest": before.local_digest,
    }
    if expected == "REJECT":
        with pytest.raises(
            PrivateContextDeltaRejected, match="scope reassignment",
        ):
            review_private_context_delta(before, after, **kwargs)
    else:
        delta = review_private_context_delta(before, after, **kwargs)
        assert delta.change_state == expected
        _deny_delta(delta)
        assert "secret-" not in repr(delta)
        assert "secret-" not in repr(new_binding)


def test_same_content_different_request_identity_requires_distinct_binding():
    preview = _preview(_item(1, "private"))
    first = bind_offline_context_request(_REQUEST, preview)
    second = bind_offline_context_request("ctxreq_" + "2" * 64, preview)
    assert first.context_digest == second.context_digest
    assert first.binding_digest != second.binding_digest
    _deny_binding(first)
    _deny_binding(second)
