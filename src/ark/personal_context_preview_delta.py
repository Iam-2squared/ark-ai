"""Content-free Personal Context preview delta across synthetic restart epochs.

Two independently provided previews may represent a changed or stale local
context. This reader compares canonical fixture previews without exporting
content or authorizing its reuse, deletion or external processing. A digest
computed on the same machine is NOT consent, provenance or trusted time.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .personal_context_offline_preview import (
    OfflineContextPreview,
    OfflineContextPreviewRejected,
    _assert_original_preview_denials,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_REC = re.compile(r"rec_[0-9a-f]{32}\Z")
_SOURCE_DOMAIN = b"ARK-local-context-fixture-preview-v1\0"
_DELTA_DOMAIN = b"ARK-personal-context-private-delta-v1\0"
_MAX_BYTES = 65536
_MAX_RECORDS = 32
_MAX_CONTENT_BYTES = 4096


class PrivateContextDeltaRejected(ValueError):
    """A private preview pair cannot be reviewed without disclosure risk."""


@dataclass(frozen=True, slots=True)
class PrivateContextDelta:
    prior_digest: str
    current_digest: str
    change_state: str
    added_count: int
    removed_count: int
    changed_count: int
    retained_count: int
    comparison_sha256: str

    @property
    def reuse_authorized(self) -> bool:
        return False

    @property
    def deletion_authorized(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def external_export_authorized(self) -> bool:
        return False


_PREVIEW = OfflineContextPreview
_RESULT = PrivateContextDelta
_FIELDS = ("owner_digest", "record_ids", "canonical_local_json", "local_digest")
_DENIALS = ("consent_verified", "external_export_authorized",
            "tool_dispatch_authorized", "retention_authorized")
_RESULT_DENIALS = ("reuse_authorized", "deletion_authorized",
                   "consent_verified", "external_export_authorized")
_ORIGINAL_SLOTS = tuple(
    (cls, name, vars(cls).get(name))
    for cls, names in (
        (_PREVIEW, _FIELDS + _DENIALS + ("__new__", "__init__", "__getattribute__")),
        (_RESULT, tuple(_RESULT.__dataclass_fields__) + _RESULT_DENIALS
         + ("__new__", "__init__", "__getattribute__")),
    ) for name in names
)
_ORIGINAL_CODECS = (hashlib.sha256, json.loads, json.dumps)
_ORIGINAL_MODULES = (hashlib, json)
_ORIGINAL_PREVIEW_GUARD = _assert_original_preview_denials
_ORIGINAL_CONSTANTS = (_SHA, _REC, _SOURCE_DOMAIN, _DELTA_DOMAIN,
                       _MAX_BYTES, _MAX_RECORDS, _MAX_CONTENT_BYTES)


def _require_originals() -> None:
    # Reject a rebound private preview validator before executing that hook.
    if _assert_original_preview_denials is not _ORIGINAL_PREVIEW_GUARD:
        raise PrivateContextDeltaRejected("private delta protocol changed")
    try:
        _ORIGINAL_PREVIEW_GUARD()
    except OfflineContextPreviewRejected as exc:
        raise PrivateContextDeltaRejected("preview source authority changed") from exc
    if (
        (hashlib, json) != _ORIGINAL_MODULES
        or (hashlib.sha256, json.loads, json.dumps) != _ORIGINAL_CODECS
        or _parse is not _ORIGINAL_PARSE
        or _duplicate_refusal is not _ORIGINAL_DUPLICATE_REFUSAL
        or (_SHA, _REC, _SOURCE_DOMAIN, _DELTA_DOMAIN,
            _MAX_BYTES, _MAX_RECORDS, _MAX_CONTENT_BYTES) != _ORIGINAL_CONSTANTS
        or type(_MAX_BYTES) is not int or type(_MAX_RECORDS) is not int
        or type(_MAX_CONTENT_BYTES) is not int
        or any(vars(cls).get(name) is not old
               for cls, name, old in _ORIGINAL_SLOTS)
    ):
        raise PrivateContextDeltaRejected("private delta protocol changed")


def _duplicate_refusal(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise PrivateContextDeltaRejected("duplicate private preview key")
        result[key] = value
    return result


def _parse(
    preview: OfflineContextPreview, owner: str, scopes: tuple[str, ...],
) -> tuple[tuple[str, str, str], ...]:
    _require_originals()
    if type(preview) is not _PREVIEW:
        raise PrivateContextDeltaRejected("exact private preview required")
    original = tuple(getattr(preview, name) for name in _FIELDS)

    def stable() -> None:
        _require_originals()
        if any(current is not first for current, first in zip(
            (preview.owner_digest, preview.record_ids,
             preview.canonical_local_json, preview.local_digest),
            original, strict=True,
        )):
            raise PrivateContextDeltaRejected("private preview epoch changed")

    owner_digest, record_ids, raw, local_digest = original
    if (
        type(owner_digest) is not str or owner_digest != owner
        or type(record_ids) is not tuple
        or not 1 <= len(record_ids) <= _MAX_RECORDS
        or type(raw) is not str or len(raw) > _MAX_BYTES
        or type(local_digest) is not str or _SHA.fullmatch(local_digest) is None
    ):
        raise PrivateContextDeltaRejected("private preview shape or owner mismatch")
    if record_ids != tuple(sorted(set(record_ids))):
        raise PrivateContextDeltaRejected("private preview IDs are not unique and sorted")
    try:
        body = raw.encode("ascii", "strict")
    except UnicodeError as exc:
        raise PrivateContextDeltaRejected("noncanonical private preview bytes") from exc
    if len(body) > _MAX_BYTES:
        raise PrivateContextDeltaRejected("private preview byte budget exceeded")
    stable()
    if hashlib.sha256(_SOURCE_DOMAIN + body).hexdigest() != local_digest:
        raise PrivateContextDeltaRejected("private preview digest mismatch")
    stable()
    try:
        decoded = json.loads(
            raw, object_pairs_hook=_duplicate_refusal,
            parse_constant=lambda _: (_ for _ in ()).throw(
                PrivateContextDeltaRejected("nonfinite private preview number")
            ),
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        if type(exc) is PrivateContextDeltaRejected:
            raise
        raise PrivateContextDeltaRejected("private preview JSON invalid") from exc
    stable()
    if (
        type(decoded) is not dict or set(decoded) != {"owner_digest", "records"}
        or decoded["owner_digest"] != owner
        or type(decoded["records"]) is not list
        or len(decoded["records"]) != len(record_ids)
    ):
        raise PrivateContextDeltaRejected("private preview JSON shape mismatch")
    encoded = json.dumps(decoded, ensure_ascii=True, sort_keys=True,
                         separators=(",", ":"), allow_nan=False)
    stable()
    if encoded != raw:
        raise PrivateContextDeltaRejected("private preview JSON not canonical")

    out: list[tuple[str, str, str]] = []
    for expected, item in zip(record_ids, decoded["records"], strict=True):
        if type(item) is not dict or set(item) != {
            "record_id", "scope_digest", "content"
        }:
            raise PrivateContextDeltaRejected("private preview record schema mismatch")
        record_id, scope, content = (
            item["record_id"], item["scope_digest"], item["content"],
        )
        if (
            type(record_id) is not str or _REC.fullmatch(record_id) is None
            or record_id != expected or type(scope) is not str
            or _SHA.fullmatch(scope) is None or scope not in scopes
            or type(content) is not str
        ):
            raise PrivateContextDeltaRejected("private preview record identity mismatch")
        if len(content) > _MAX_CONTENT_BYTES:
            raise PrivateContextDeltaRejected("private preview content budget exceeded")
        try:
            content_bytes = content.encode("utf-8", "strict")
        except UnicodeError as exc:
            raise PrivateContextDeltaRejected("private preview content Unicode invalid") from exc
        if len(content_bytes) > _MAX_CONTENT_BYTES:
            raise PrivateContextDeltaRejected("private preview content budget exceeded")
        out.append((record_id, scope, hashlib.sha256(content_bytes).hexdigest()))
        stable()
    if record_ids != tuple(sorted(set(record_ids))):
        raise PrivateContextDeltaRejected("private preview IDs are not unique and sorted")
    for name in _DENIALS:
        _require_originals()
        if getattr(preview, name) is not False:
            raise PrivateContextDeltaRejected("private preview gained authority")
        stable()
    return tuple(out)


# Snapshot the parsing and duplicate-key boundary after their definitions.
# Neither a synthetic fixture callback nor a local monkeypatch may silently
# substitute a no-op parser before the private JSON is inspected.
_ORIGINAL_PARSE = _parse
_ORIGINAL_DUPLICATE_REFUSAL = _duplicate_refusal


def review_private_context_delta(
    prior: OfflineContextPreview,
    current: OfflineContextPreview,
    *,
    owner_digest: str,
    allowed_scope_digests: tuple[str, ...],
    independently_retained_prior_digest: str,
) -> PrivateContextDelta:
    """Return counts and hashes only, never text or automatic reuse authority."""
    _require_originals()
    if (
        type(owner_digest) is not str or _SHA.fullmatch(owner_digest) is None
        or type(allowed_scope_digests) is not tuple
        or not 1 <= len(allowed_scope_digests) <= _MAX_RECORDS
        or any(type(scope) is not str or _SHA.fullmatch(scope) is None
               for scope in allowed_scope_digests)
        or allowed_scope_digests != tuple(sorted(set(allowed_scope_digests)))
        or type(independently_retained_prior_digest) is not str
        or _SHA.fullmatch(independently_retained_prior_digest) is None
    ):
        raise PrivateContextDeltaRejected("invalid owner/scope or prior digest")
    previous = _parse(prior, owner_digest, allowed_scope_digests)
    observed = _parse(current, owner_digest, allowed_scope_digests)
    _require_originals()
    if prior.local_digest != independently_retained_prior_digest:
        raise PrivateContextDeltaRejected("retained private preview prefix mismatch")
    old_map = {identity: (scope, digest) for identity, scope, digest in previous}
    new_map = {identity: (scope, digest) for identity, scope, digest in observed}
    shared = set(old_map) & set(new_map)
    # A changed scope for the same record is not routine content editing.
    # A caller must review it as a new identity under its own scoped ledger.
    if any(old_map[identity][0] != new_map[identity][0] for identity in shared):
        raise PrivateContextDeltaRejected("private context scope reassignment refused")
    added = len(new_map.keys() - old_map.keys())
    removed = len(old_map.keys() - new_map.keys())
    changed = sum(old_map[identity][1] != new_map[identity][1] for identity in shared)
    retained = len(shared) - changed
    state = "UNCHANGED" if added + removed + changed == 0 else "REVIEW_REQUIRED"
    payload = json.dumps(
        [prior.local_digest, current.local_digest, previous, observed, state],
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256(_DELTA_DOMAIN + payload).hexdigest()
    _require_originals()
    # This repeat validates the initial exact preview epoch after serializing.
    if (_parse(prior, owner_digest, allowed_scope_digests) != previous
            or _parse(current, owner_digest, allowed_scope_digests) != observed
            or prior.local_digest != independently_retained_prior_digest):
        raise PrivateContextDeltaRejected("private preview changed during comparison")
    result = _RESULT(
        prior.local_digest, current.local_digest, state,
        added, removed, changed, retained, digest,
    )
    _require_originals()
    if (
        type(result) is not _RESULT
        or any(getattr(result, name) is not False for name in _RESULT_DENIALS)
    ):
        raise PrivateContextDeltaRejected("private delta gained authority")
    return result
