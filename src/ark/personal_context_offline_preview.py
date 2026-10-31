"""Bounded, unprivileged local-only context preview from explicit fixtures.

The caller's owner, scopes, timestamps and content hashes are not authenticated.
No Memory database, permission grant, real user profile, network or model is
accessed. This may not be connected to external export or live Tool execution.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_RECORD = re.compile(r"rec_[0-9a-f]{32}\Z")
_MAX = 2**63 - 1
_MAX_RECORDS = 32
_MAX_CONTENT = 4_096
_MAX_TOTAL = 16_384
# JSON string escaping can expand accepted UTF-8 fixture bytes substantially.
_MAX_SERIALIZED_BYTES = 65_536
_DOMAIN = b"ARK-local-context-fixture-preview-v1\0"


class OfflineContextPreviewRejected(ValueError):
    """Fixture context is stale, out of scope, altered or unbounded."""


@dataclass(frozen=True, slots=True)
class OfflineContextFixture:
    record_id: str
    owner_digest: str
    scope_digest: str
    content: str = field(repr=False)
    content_sha256: str
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class OfflineContextPreview:
    owner_digest: str
    record_ids: tuple[str, ...]
    canonical_local_json: str = field(repr=False)
    local_digest: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def external_export_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def retention_authorized(self) -> bool:
        return False


_PREVIEW_RESULT_TYPE = OfflineContextPreview


def build_offline_context_preview(
    fixtures: tuple[OfflineContextFixture, ...],
    *,
    owner_digest: str,
    allowed_scope_digests: tuple[str, ...],
    observed_at_ms: int,
) -> OfflineContextPreview:
    """Make a bounded JSON *local fixture* with strict owner/scope isolation.

    Passing an allowlist is not proof of human consent or a fresh revocation
    check. All fixtures must be validated; never silently accept only the
    seemingly safe subset of a mixed-owner or stale batch.
    """
    original = (fixtures, owner_digest, allowed_scope_digests, observed_at_ms)
    if (
        type(fixtures) is not tuple or not 1 <= len(fixtures) <= _MAX_RECORDS
        or type(owner_digest) is not str or _DIGEST.fullmatch(owner_digest) is None
        or type(allowed_scope_digests) is not tuple
        or not 1 <= len(allowed_scope_digests) <= _MAX_RECORDS
        or any(type(x) is not str or _DIGEST.fullmatch(x) is None
               for x in allowed_scope_digests)
        or allowed_scope_digests != tuple(sorted(set(allowed_scope_digests)))
        or type(observed_at_ms) is not int or not 0 <= observed_at_ms <= _MAX
        or any(type(x) is not OfflineContextFixture for x in fixtures)
    ):
        raise OfflineContextPreviewRejected("invalid bounded context fixture batch")
    pinned = tuple((entry, (
        entry.record_id, entry.owner_digest, entry.scope_digest,
        entry.content, entry.content_sha256, entry.expires_at_ms,
    )) for entry in fixtures)

    def assert_epoch() -> None:
        if any(
            current is not prior
            for current, prior in zip(
                (fixtures, owner_digest, allowed_scope_digests, observed_at_ms),
                original, strict=True,
            )
        ) or any(
            fixtures[i] is not record
            or any(
                now is not was
                for now, was in zip((
                    record.record_id, record.owner_digest, record.scope_digest,
                    record.content, record.content_sha256, record.expires_at_ms,
                ), carriers, strict=True)
            )
            for i, (record, carriers) in enumerate(pinned)
        ):
            raise OfflineContextPreviewRejected("context fixture changed during preview")

    assert_epoch()
    entries = []
    ids = []
    total = 0
    for _record, captured in pinned:
        assert_epoch()
        record_id, owner, scope, content, content_sha, expires = captured
        if (
            type(record_id) is not str or _RECORD.fullmatch(record_id) is None
            or type(owner) is not str or owner != owner_digest
            or type(scope) is not str or scope not in allowed_scope_digests
            or type(content) is not str or len(content) > _MAX_CONTENT
            or type(content_sha) is not str or _DIGEST.fullmatch(content_sha) is None
            or type(expires) is not int or not observed_at_ms < expires <= _MAX
        ):
            raise OfflineContextPreviewRejected("stale or mismatched context record")
        try:
            raw = content.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise OfflineContextPreviewRejected("invalid context Unicode") from exc
        if len(raw) > _MAX_CONTENT:
            raise OfflineContextPreviewRejected("context content byte budget exceeded")
        total += len(raw)
        if total > _MAX_TOTAL:
            raise OfflineContextPreviewRejected("context preview total byte budget exceeded")
        if hashlib.sha256(raw).hexdigest() != content_sha:
            raise OfflineContextPreviewRejected("context content digest mismatch")
        assert_epoch()
        ids.append(record_id)
        entries.append({"record_id": record_id, "scope_digest": scope, "content": content})
    if ids != sorted(set(ids)):
        raise OfflineContextPreviewRejected("duplicate or unordered context identity")
    assert_epoch()
    expected_payload = {"owner_digest": owner_digest, "records": entries}
    payload = json.dumps(
        expected_payload,
        sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"),
    )
    assert_epoch()
    # A buggy/injected serializer can emit syntactically valid JSON with a
    # different owner, record or content. Never hash-and-return such bytes as
    # though they were the exact caller-reviewed fixture epoch.
    try:
        decoded = json.loads(payload)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise OfflineContextPreviewRejected("context preview serialization invalid") from exc
    assert_epoch()
    if type(decoded) is not dict or decoded != expected_payload:
        raise OfflineContextPreviewRejected("context preview serialization disagrees with fixtures")
    canonical = json.dumps(
        decoded, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    )
    assert_epoch()
    if type(payload) is not str or payload != canonical:
        raise OfflineContextPreviewRejected("context preview serialization is not canonical")
    serialized = payload.encode("utf-8")
    if len(serialized) > _MAX_SERIALIZED_BYTES:
        raise OfflineContextPreviewRejected("serialized context preview budget exceeded")
    digest = hashlib.sha256(_DOMAIN + serialized).hexdigest()
    assert_epoch()
    record_ids = tuple(ids)
    result = OfflineContextPreview(owner_digest, record_ids, payload, digest)
    assert_epoch()
    if (
        type(result) is not _PREVIEW_RESULT_TYPE
        or result.owner_digest is not owner_digest
        or result.record_ids is not record_ids
        or result.canonical_local_json is not payload
        or result.local_digest is not digest
        or result.consent_verified is not False
        or result.external_export_authorized is not False
        or result.tool_dispatch_authorized is not False
        or result.retention_authorized is not False
    ):
        raise OfflineContextPreviewRejected("constructed context preview changed")
    # Reading a denial-only authority descriptor is a callback boundary:
    # the last getter might have changed a previously checked input or
    # result field. Never return a private fixture preview from that epoch.
    assert_epoch()
    if (
        type(result) is not _PREVIEW_RESULT_TYPE
        or result.owner_digest is not owner_digest
        or result.record_ids is not record_ids
        or result.canonical_local_json is not payload
        or result.local_digest is not digest
    ):
        raise OfflineContextPreviewRejected(
            "context preview changed after authority review"
        )
    assert_epoch()
    return result


def verify_offline_context_preview(
    report: OfflineContextPreview,
    fixtures: tuple[OfflineContextFixture, ...],
    *,
    owner_digest: str,
    allowed_scope_digests: tuple[str, ...],
    observed_at_ms: int,
    retained_local_digest: str,
) -> None:
    """Verify an independently retained synthetic preview without disclosure.

    This only checks caller-provided fixture bytes, scope and expiry against
    the detached receipt. It does not authenticate user consent, ownership,
    live Memory rows, current time, or permission to export these contents.
    """
    if (
        type(report) is not _PREVIEW_RESULT_TYPE
        or type(retained_local_digest) is not str
        or _DIGEST.fullmatch(retained_local_digest) is None
        or type(fixtures) is not tuple
    ):
        raise OfflineContextPreviewRejected("exact retained context preview required")
    originals = tuple(fixtures)
    captured = tuple(
        (item, item.record_id, item.owner_digest, item.scope_digest,
         item.content, item.content_sha256, item.expires_at_ms)
        for item in originals if type(item) is OfflineContextFixture
    )

    def stable_sources() -> None:
        if (
            type(fixtures) is not tuple
            or len(originals) != len(fixtures)
            or len(captured) != len(originals)
            or any(
                fixtures[i] is not fields[0]
                or any(now is not old for now, old in zip(
                    (fields[0].record_id, fields[0].owner_digest,
                     fields[0].scope_digest, fields[0].content,
                     fields[0].content_sha256, fields[0].expires_at_ms),
                    fields[1:], strict=True,
                ))
                for i, fields in enumerate(captured)
            )
        ):
            raise OfflineContextPreviewRejected("retained fixture changed during review")

    expected = build_offline_context_preview(
        fixtures, owner_digest=owner_digest,
        allowed_scope_digests=allowed_scope_digests,
        observed_at_ms=observed_at_ms,
    )
    stable_sources()

    def exact_report() -> bool:
        return (
            type(report) is _PREVIEW_RESULT_TYPE
            and type(report.owner_digest) is str
            and report.owner_digest == expected.owner_digest
            and type(report.record_ids) is tuple
            and all(type(name) is str for name in report.record_ids)
            and report.record_ids == expected.record_ids
            and type(report.canonical_local_json) is str
            and report.canonical_local_json == expected.canonical_local_json
            and type(report.local_digest) is str
            and report.local_digest == expected.local_digest
            and report.local_digest == retained_local_digest
        )

    if not exact_report():
        raise OfflineContextPreviewRejected("retained context preview mismatch")
    for flag in (
        "consent_verified", "external_export_authorized",
        "tool_dispatch_authorized", "retention_authorized",
    ):
        if getattr(report, flag) is not False:
            raise OfflineContextPreviewRejected(
                "retained context preview gained authority"
            )
    # Even a denial getter that returns False may mutate the untrusted
    # fixture, record scope, or private serialized result.
    stable_sources()
    if not exact_report():
        raise OfflineContextPreviewRejected(
            "retained context preview changed after denial"
        )
    latest = build_offline_context_preview(
        fixtures, owner_digest=owner_digest,
        allowed_scope_digests=allowed_scope_digests,
        observed_at_ms=observed_at_ms,
    )
    stable_sources()
    if (
        not exact_report()
        or type(latest) is not _PREVIEW_RESULT_TYPE
        or latest.local_digest != expected.local_digest
        or latest.canonical_local_json != expected.canonical_local_json
        or latest.record_ids != expected.record_ids
    ):
        raise OfflineContextPreviewRejected(
            "retained context fixtures changed during verification"
        )
