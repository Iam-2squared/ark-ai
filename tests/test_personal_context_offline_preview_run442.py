"""Local-only synthetic context preview, no external consent or live memory."""

import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark import personal_context_offline_preview as mod

OWNER = "a" * 64
OTHER = "b" * 64
SCOPE = "c" * 64
SCOPE_2 = "d" * 64


def fixture(number: int = 1, text: str = "test", **changes):
    baseline = mod.OfflineContextFixture(
        "rec_" + format(number, "032x"), OWNER, SCOPE, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 1100,
    )
    return replace(baseline, **changes)


def build(rows, **kwargs):
    return mod.build_offline_context_preview(
        rows, owner_digest=kwargs.get("owner", OWNER),
        allowed_scope_digests=kwargs.get("scopes", (SCOPE,)),
        observed_at_ms=kwargs.get("now", 1000),
    )


def test_canonical_local_json_and_explicit_non_authority():
    result = build((fixture(text="x\\n\"y"),))
    data = json.loads(result.canonical_local_json)
    assert data["owner_digest"] == OWNER
    assert data["records"][0]["content"] == 'x\\n"y'
    assert result.record_ids == ("rec_" + format(1, "032x"),)
    assert len(result.local_digest) == 64
    assert not result.consent_verified
    assert not result.external_export_authorized
    assert not result.tool_dispatch_authorized
    assert not result.retention_authorized
    assert result == build((fixture(text="x\\n\"y"),))


def test_sorted_multiple_scopes_are_explicit_and_bounded():
    rows = (fixture(1), fixture(2, "world", scope_digest=SCOPE_2))
    preview = build(rows, scopes=(SCOPE, SCOPE_2))
    assert len(preview.record_ids) == 2
    assert len(json.loads(preview.canonical_local_json)["records"]) == 2


@pytest.mark.parametrize("changes", [
    {"owner_digest": OTHER}, {"scope_digest": OTHER},
    {"record_id": "bad"}, {"record_id": None},
    {"content": None}, {"content": True},
    {"content": "\ud800"},
    {"content": "a" * 4097}, {"content": "🔥" * 1100},
    {"content_sha256": OTHER}, {"content_sha256": "bad"},
    {"expires_at_ms": 1000}, {"expires_at_ms": 0},
    {"expires_at_ms": True}, {"expires_at_ms": 2**63},
])
def test_invalid_item_rejected(changes):
    with pytest.raises(mod.OfflineContextPreviewRejected):
        build((fixture(**changes),))


@pytest.mark.parametrize("rows,kwargs", [
    ((), {}), ("not-a-tuple", {}),
    ((fixture(), fixture()), {}),
    ((fixture(2), fixture(1)), {}),
    ((fixture(),), {"owner": OTHER}),
    ((fixture(),), {"owner": True}),
    ((fixture(),), {"scopes": (OTHER,)}),
    ((fixture(),), {"scopes": (SCOPE, SCOPE)}),
    ((fixture(),), {"scopes": (SCOPE_2, SCOPE)}),
    ((fixture(),), {"scopes": []}),
    ((fixture(),), {"now": 1100}),
    ((fixture(),), {"now": -1}),
    ((fixture(),), {"now": True}),
])
def test_batch_rejected_fail_closed(rows, kwargs):
    with pytest.raises(mod.OfflineContextPreviewRejected):
        build(rows, **kwargs)


def test_total_utf8_budget_fail_closed():
    rows = tuple(fixture(i, text="a" * 4096) for i in range(1, 6))
    with pytest.raises(mod.OfflineContextPreviewRejected, match="total byte"):
        build(rows)


def test_too_many_records_are_denied():
    rows = tuple(fixture(i) for i in range(1, 34))
    with pytest.raises(mod.OfflineContextPreviewRejected):
        build(rows)


def test_reflective_content_mutation_during_digest(monkeypatch):
    item = fixture()
    prior = mod.hashlib.sha256

    def reentrant(value):
        object.__setattr__(item, "content", "retargeted")
        return prior(value)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.OfflineContextPreviewRejected, match="changed"):
        build((item,))


def test_same_value_different_carrier_rejected(monkeypatch):
    item = fixture(text="some-long-context-string")
    prior = mod.hashlib.sha256

    def reentrant(value):
        copy = bytes(item.content, "utf-8").decode("utf-8")
        assert copy == item.content
        object.__setattr__(item, "content", copy)
        return prior(value)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.OfflineContextPreviewRejected, match="changed"):
        build((item,))


def test_record_subclass_rejected():
    class SubRecord(mod.OfflineContextFixture):
        pass

    original = fixture()
    item = SubRecord(
        original.record_id, original.owner_digest, original.scope_digest,
        original.content, original.content_sha256, original.expires_at_ms,
    )
    with pytest.raises(mod.OfflineContextPreviewRejected):
        build((item,))
