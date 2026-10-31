"""Post-authority Personal Context receipt custody for synthetic fixtures."""

from __future__ import annotations

import hashlib

import pytest

import ark.personal_context_request_binding as binding
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)

_REQUEST = "ctxreq_" + "1" * 64
_OWNER = "a" * 64
_SCOPE = "b" * 64


def _preview():
    content = "private local-only fixture"
    fixture = OfflineContextFixture(
        "rec_" + "2" * 32,
        _OWNER,
        _SCOPE,
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        1000,
    )
    return build_offline_context_preview(
        (fixture,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=100,
    )


@pytest.mark.parametrize("target", ("preview", "result"))
def test_false_retention_getter_cannot_mutate_receipt_after_first_check(
    monkeypatch, target,
):
    preview = _preview()

    def late_mutation(result):
        if target == "preview":
            object.__setattr__(preview, "owner_digest", "f" * 64)
        else:
            object.__setattr__(result, "binding_digest", "f" * 64)
        return False

    monkeypatch.setattr(
        binding._BINDING_TYPE,
        "retention_authorized",
        property(late_mutation),
    )
    with pytest.raises(
        binding.OfflineContextBindingRejected, match="changed",
    ):
        binding.bind_offline_context_request(_REQUEST, preview)


def test_local_only_request_binding_remains_deterministic_and_unauthorized():
    preview = _preview()
    left = binding.bind_offline_context_request(_REQUEST, preview)
    right = binding.bind_offline_context_request(_REQUEST, preview)
    assert left == right
    assert left.consent_verified is False
    assert left.retention_authorized is False
    assert left.external_export_authorized is False
