"""Content-free Personal Context preview changes require explicit review."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_preview_delta import (
    PrivateContextDeltaRejected,
    review_private_context_delta,
)

_OWNER = "a" * 64
_OTHER_OWNER = "d" * 64
_SCOPE = "b" * 64
_OTHER_SCOPE = "c" * 64
_SCOPES = (_SCOPE, _OTHER_SCOPE)
_DOMAIN = b"ARK-local-context-fixture-preview-v1\0"


def _fixture(number: int, content: str, *, scope: str = _SCOPE) -> OfflineContextFixture:
    return OfflineContextFixture(
        record_id=f"rec_{number:032x}",
        owner_digest=_OWNER,
        scope_digest=scope,
        content=content,
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        expires_at_ms=1000,
    )


def _preview(*records: OfflineContextFixture):
    return build_offline_context_preview(
        tuple(records), owner_digest=_OWNER, allowed_scope_digests=_SCOPES,
        observed_at_ms=50,
    )


def _compare(before, after, *, retained: str | None = None, scopes=_SCOPES):
    return review_private_context_delta(
        before, after, owner_digest=_OWNER, allowed_scope_digests=scopes,
        independently_retained_prior_digest=(
            before.local_digest if retained is None else retained
        ),
    )


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    (
        ((_fixture(1, "hello"),), (_fixture(1, "hello"),), (0, 0, 0, 1, "UNCHANGED")),
        ((_fixture(1, "hello"),), (_fixture(1, "updated"),), (0, 0, 1, 0, "REVIEW_REQUIRED")),
        ((_fixture(1, "hello"),), (_fixture(1, "hello"), _fixture(2, "new")),
         (1, 0, 0, 1, "REVIEW_REQUIRED")),
        ((_fixture(1, "hello"), _fixture(2, "removed")), (_fixture(1, "hello"),),
         (0, 1, 0, 1, "REVIEW_REQUIRED")),
        ((_fixture(1, "old"), _fixture(2, "removed")),
         (_fixture(1, "new"), _fixture(3, "added")),
         (1, 1, 1, 0, "REVIEW_REQUIRED")),
        ((_fixture(1, "日本語"),), (_fixture(1, "日本語"),),
         (0, 0, 0, 1, "UNCHANGED")),
    ),
)
def test_content_free_change_classification(old, new, expected) -> None:
    before, after = _preview(*old), _preview(*new)
    report = _compare(before, after)
    assert (report.added_count, report.removed_count, report.changed_count,
            report.retained_count, report.change_state) == expected
    assert report.reuse_authorized is False
    assert report.deletion_authorized is False
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert len(report.comparison_sha256) == 64
    assert "hello" not in repr(report)
    assert _compare(before, after) == report


@pytest.mark.parametrize(
    ("condition", "expected"),
    (
        ("wrong-owner", "shape or owner"),
        ("foreign-owner-current", "shape or owner"),
        ("stale-retained", "retained"),
        ("wrong-scope-allowlist", "record identity"),
        ("scope-migration", "scope reassignment"),
        ("bad-raw-digest", "digest mismatch"),
        ("bad-digest-shape", "shape or owner"),
        ("duplicate-json-key", "duplicate"),
        ("noncanonical-json", "not canonical"),
        ("record-id-mismatch", "record identity"),
        ("record-set-incorrect", "JSON shape"),
        ("extra-json-field", "JSON shape"),
        ("bad-content-utf8", "content Unicode"),
        ("content-too-large", "content budget"),
        ("no-ids", "shape or owner"),
        ("dupe-ids", "not unique"),
        ("invalid-scope-list", "invalid owner"),
        ("invalid-retained-type", "invalid owner"),
    ),
)
def test_malformed_or_cross_scope_private_snapshots_are_refused(
    condition: str, expected: str,
) -> None:
    before = _preview(_fixture(1, "secret"))
    after = _preview(_fixture(1, "secret"))
    retained = before.local_digest
    scopes = _SCOPES
    owner = _OWNER

    def forged_raw(report, raw: str):
        return replace(report, canonical_local_json=raw,
                       local_digest=hashlib.sha256(_DOMAIN + raw.encode("ascii")).hexdigest())

    if condition == "wrong-owner":
        before = replace(before, owner_digest=_OTHER_OWNER)
    elif condition == "foreign-owner-current":
        after = replace(after, owner_digest=_OTHER_OWNER)
    elif condition == "stale-retained":
        retained = "f" * 64
    elif condition == "wrong-scope-allowlist":
        scopes = (_OTHER_SCOPE,)
    elif condition == "scope-migration":
        after = _preview(_fixture(1, "secret", scope=_OTHER_SCOPE))
    elif condition == "bad-raw-digest":
        after = replace(after, canonical_local_json=after.canonical_local_json + " ")
    elif condition == "bad-digest-shape":
        after = replace(after, local_digest="x")
    elif condition == "duplicate-json-key":
        raw = after.canonical_local_json.replace(
            '"owner_digest":', '"owner_digest":"x","owner_digest":',
        )
        after = forged_raw(after, raw)
    elif condition == "noncanonical-json":
        raw = json.dumps(json.loads(after.canonical_local_json), indent=2)
        after = forged_raw(after, raw)
    elif condition == "record-id-mismatch":
        decoded = json.loads(after.canonical_local_json)
        decoded["records"][0]["record_id"] = "rec_" + "f" * 32
        raw = json.dumps(decoded, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        after = forged_raw(after, raw)
    elif condition == "record-set-incorrect":
        decoded = json.loads(after.canonical_local_json)
        decoded["records"] = []
        raw = json.dumps(decoded, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        after = forged_raw(after, raw)
    elif condition == "extra-json-field":
        decoded = json.loads(after.canonical_local_json)
        decoded["opaque_unexpected"] = True
        raw = json.dumps(decoded, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        after = forged_raw(after, raw)
    elif condition == "bad-content-utf8":
        decoded = json.loads(after.canonical_local_json)
        decoded["records"][0]["content"] = chr(0xD800)
        raw = json.dumps(decoded, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        after = forged_raw(after, raw)
    elif condition == "content-too-large":
        decoded = json.loads(after.canonical_local_json)
        decoded["records"][0]["content"] = "z" * 4097
        raw = json.dumps(decoded, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        after = forged_raw(after, raw)
    elif condition == "no-ids":
        after = replace(after, record_ids=())
    elif condition == "dupe-ids":
        after = replace(after, record_ids=after.record_ids * 2)
    elif condition == "invalid-scope-list":
        scopes = (_SCOPE, _SCOPE)
    elif condition == "invalid-retained-type":
        retained = True
    with pytest.raises(PrivateContextDeltaRejected, match=expected):
        review_private_context_delta(
            before, after, owner_digest=owner,
            allowed_scope_digests=scopes,
            independently_retained_prior_digest=retained,
        )


def test_private_delta_never_exposes_input_text_or_identifiers_in_result() -> None:
    secret = "private-sensitive-preview-text"
    before = _preview(_fixture(1, secret))
    after = _preview(_fixture(1, secret + "-changed"))
    result = _compare(before, after)
    assert secret not in repr(result)
    assert _fixture(1, secret).record_id not in repr(result)
    assert result.changed_count == 1


@pytest.mark.parametrize("modified", ["owner", "text", "digest", "ids"])
def test_local_report_reflection_is_refused(modified: str) -> None:
    old = _preview(_fixture(1, "a"))
    current = _preview(_fixture(1, "b"))
    if modified == "owner":
        object.__setattr__(old, "owner_digest", _OTHER_OWNER)
    elif modified == "text":
        object.__setattr__(current, "canonical_local_json", "{}")
    elif modified == "digest":
        object.__setattr__(current, "local_digest", "0" * 64)
    else:
        object.__setattr__(old, "record_ids", ("rec_" + "e" * 32,))
    with pytest.raises(PrivateContextDeltaRejected):
        _compare(old, current)
