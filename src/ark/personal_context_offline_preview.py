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
    payload = json.dumps(
        {"owner_digest": owner_digest, "records": entries},
        sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"),
    )
    assert_epoch()
    digest = hashlib.sha256(_DOMAIN + payload.encode("utf-8")).hexdigest()
    assert_epoch()
    result = OfflineContextPreview(owner_digest, tuple(ids), payload, digest)
    assert_epoch()
    if (
        type(result) is not OfflineContextPreview
        or result.owner_digest is not owner_digest
        or result.record_ids != tuple(ids)
        or result.canonical_local_json is not payload
        or result.local_digest is not digest
    ):
        raise OfflineContextPreviewRejected("constructed context preview changed")
    return result
