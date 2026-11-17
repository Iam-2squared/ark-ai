"""Bound JSON-escaped privacy preview size without relaxing raw-content budgets.

Synthetic local strings only; accepted previews are diagnostics and provide no
authenticated consent, external export, retention or ToolBackend authority.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreviewRejected,
    build_offline_context_preview,
    verify_offline_context_preview,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _records(character: str, count: int) -> tuple[OfflineContextFixture, ...]:
    content = character * 4096
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return tuple(
        OfflineContextFixture(
            "rec_" + f"{index:032x}", _OWNER, _SCOPE,
            content, digest, 2000,
        )
        for index in range(count)
    )


@pytest.mark.parametrize("count", (1, 2, 3, 4))
@pytest.mark.parametrize("character", ("\x00", "\x1f"))
def test_json_control_escaping_respects_serialized_budget(
    character: str, count: int,
) -> None:
    # Three 4096-byte rows are under the 16384-byte source-data budget,
    # but each byte expands to six ASCII JSON characters.
    rows = _records(character, count)
    if count >= 3:
        with pytest.raises(
            OfflineContextPreviewRejected, match="serialized context preview budget"
        ):
            build_offline_context_preview(
                rows, owner_digest=_OWNER,
                allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
            )
        return

    report = build_offline_context_preview(
        rows, owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
    )
    assert len(report.canonical_local_json.encode("utf-8")) <= 65_536
    assert len(report.record_ids) == count
    verify_offline_context_preview(
        report, rows, owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
        retained_local_digest=report.local_digest,
    )
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False


@pytest.mark.parametrize("character", ("\n", "x"))
def test_four_rows_below_escaped_limit_remain_verifiable(character: str) -> None:
    rows = _records(character, 4)
    report = build_offline_context_preview(
        rows, owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
    )
    assert len(report.record_ids) == 4
    assert len(report.canonical_local_json.encode("utf-8")) <= 65_536
    verify_offline_context_preview(
        report, rows, owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=100,
        retained_local_digest=report.local_digest,
    )
