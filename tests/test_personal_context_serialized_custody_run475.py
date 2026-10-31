"""Offline personal-context fixture serialization remains bounded and inert."""

from __future__ import annotations

import hashlib
import json

import pytest

from ark import personal_context_offline_preview as preview

OWNER = "a" * 64
SCOPE = "b" * 64


def _item(index, text):
    return preview.OfflineContextFixture(
        "rec_" + f"{index:032x}", OWNER, SCOPE, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 500,
    )


def _build(items):
    return preview.build_offline_context_preview(
        items, owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,), observed_at_ms=100,
    )


def test_plain_ascii_near_raw_budget_still_supported():
    rows = tuple(_item(i, "a" * 4000) for i in range(1, 5))
    result = _build(rows)
    assert len(json.loads(result.canonical_local_json)["records"]) == 4
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.retention_authorized is False
    assert result == _build(rows)


@pytest.mark.parametrize("char", ["\x00", "\x01", "\x1f"])
def test_escaped_serialization_above_fixed_budget_is_rejected(char):
    # JSON \\u00xx escaping expands four 4,000-byte fixtures to over 96 KiB,
    # despite their original UTF-8 content fitting the 16 KiB input budget.
    rows = tuple(_item(i, char * 4000) for i in range(1, 5))
    with pytest.raises(preview.OfflineContextPreviewRejected, match="serialized"):
        _build(rows)


def test_moderate_escaped_payload_is_allowed():
    result = _build((_item(1, "\x00" * 2048),))
    assert json.loads(result.canonical_local_json)["records"][0]["content"] == "\x00" * 2048


def test_same_value_record_ids_carrier_replacement_is_rejected(monkeypatch):
    original = preview.OfflineContextPreview

    def replace_ids(*args):
        result = original(*args)
        other = tuple(list(result.record_ids))
        assert other == result.record_ids and other is not result.record_ids
        object.__setattr__(result, "record_ids", other)
        return result

    monkeypatch.setattr(preview, "OfflineContextPreview", replace_ids)
    with pytest.raises(preview.OfflineContextPreviewRejected, match="constructed"):
        _build((_item(1, "fixture"),))


@pytest.mark.parametrize(
    "property_name",
    ("consent_verified", "external_export_authorized",
     "tool_dispatch_authorized", "retention_authorized"),
)
def test_preview_can_never_claim_disclosure_or_retention_rights(
    monkeypatch, property_name,
):
    monkeypatch.setattr(
        preview.OfflineContextPreview, property_name,
        property(lambda self: True),
    )
    with pytest.raises(preview.OfflineContextPreviewRejected, match="constructed"):
        _build((_item(1, "fixture"),))
