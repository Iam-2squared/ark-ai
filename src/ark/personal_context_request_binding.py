"""Request-scoped binding for disconnected Personal Context JSON fixtures.

This receipt intentionally contains no user text. A request identifier, hash or
scope allowlist does NOT authenticate consent, enable retention, or authorize
any Tool, network, model or external use. The source preview may be expired
or revoked after construction; no live revocation authority is consulted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .personal_context_offline_preview import OfflineContextPreview

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_REQUEST = re.compile(r"ctxreq_[0-9a-f]{64}\Z")
_RECORD = re.compile(r"rec_[0-9a-f]{32}\Z")
_PREVIEW_DOMAIN = b"ARK-local-context-fixture-preview-v1\0"
_BINDING_DOMAIN = b"ARK-offline-context-request-binding-v1\0"
_PREVIEW_TYPE = OfflineContextPreview
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_LOADS = json.loads
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_RE = re
_ORIGINAL_COMPILE = re.compile
_ORIGINAL_REGEXES = (_SHA, _REQUEST, _RECORD)
_ORIGINAL_DOMAINS = (_PREVIEW_DOMAIN, _BINDING_DOMAIN)


class OfflineContextBindingRejected(ValueError):
    """Untrusted context fixture preview or request identifier is invalid."""


@dataclass(frozen=True, slots=True)
class OfflineContextRequestBinding:
    request_id: str
    owner_digest: str
    context_digest: str
    record_count: int
    binding_digest: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def revocation_freshness_verified(self) -> bool:
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


_BINDING_TYPE = OfflineContextRequestBinding
_PREVIEW_DENIALS = (
    "consent_verified", "external_export_authorized",
    "tool_dispatch_authorized", "retention_authorized",
)
_BINDING_DENIALS = (
    "consent_verified", "revocation_freshness_verified",
    "external_export_authorized", "tool_dispatch_authorized",
    "retention_authorized",
)
# A callback must never establish the baseline for a False-only authority
# descriptor: retain the original class implementations at module import.
_ORIGINAL_PREVIEW_DENIALS = tuple(
    vars(_PREVIEW_TYPE)[name] for name in _PREVIEW_DENIALS
)
_ORIGINAL_BINDING_DENIALS = tuple(
    vars(_BINDING_TYPE)[name] for name in _BINDING_DENIALS
)
# The context JSON remains private fixture text even though the receipt is
# content-free. Frozen slotted classes can acquire executable replacement
# fields or hooks; check static identities before reading private preview
# data or constructing the binding's denial-only result.
_PREVIEW_FIELDS = (
    "owner_digest", "record_ids", "canonical_local_json", "local_digest",
)
_BINDING_FIELDS = (
    "request_id", "owner_digest", "context_digest", "record_count",
    "binding_digest",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_PREVIEW_FIELDS = tuple(
    vars(_PREVIEW_TYPE)[name] for name in _PREVIEW_FIELDS
)
_ORIGINAL_BINDING_FIELDS = tuple(
    vars(_BINDING_TYPE)[name] for name in _BINDING_FIELDS
)
_ORIGINAL_PREVIEW_HOOKS = tuple(
    vars(_PREVIEW_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_BINDING_HOOKS = tuple(
    vars(_BINDING_TYPE).get(name) for name in _CARRIER_HOOKS
)


def _assert_original_private_codec() -> None:
    """Reject replaced JSON/hash/regex code before reading local-only text.

    These interpreter-local checks do not prove consent, independent capture
    provenance, source authenticity, or external tool dispatch permission.
    """
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.loads is not _ORIGINAL_LOADS
        or json.dumps is not _ORIGINAL_DUMPS
        or re is not _ORIGINAL_RE
        or re.compile is not _ORIGINAL_COMPILE
        or any(now is not prior for now, prior in zip(
            (_SHA, _REQUEST, _RECORD), _ORIGINAL_REGEXES, strict=True,
        ))
        or any(now is not prior for now, prior in zip(
            (_PREVIEW_DOMAIN, _BINDING_DOMAIN),
            _ORIGINAL_DOMAINS, strict=True,
        ))
    ):
        raise OfflineContextBindingRejected("private context binding codec changed")


def _assert_original_denials() -> None:
    _assert_original_private_codec()
    if (
        OfflineContextPreview is not _PREVIEW_TYPE
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in (
                (_PREVIEW_TYPE, _PREVIEW_FIELDS, _ORIGINAL_PREVIEW_FIELDS),
                (_BINDING_TYPE, _BINDING_FIELDS, _ORIGINAL_BINDING_FIELDS),
                (_PREVIEW_TYPE, _CARRIER_HOOKS, _ORIGINAL_PREVIEW_HOOKS),
                (_BINDING_TYPE, _CARRIER_HOOKS, _ORIGINAL_BINDING_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or any(
            vars(_PREVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _PREVIEW_DENIALS, _ORIGINAL_PREVIEW_DENIALS, strict=True,
            )
        )
    ):
        raise OfflineContextBindingRejected("context preview carrier changed")
    if (
        OfflineContextRequestBinding is not _BINDING_TYPE
        or any(
            vars(_BINDING_TYPE).get(name) is not original
            for name, original in zip(
                _BINDING_DENIALS, _ORIGINAL_BINDING_DENIALS, strict=True,
            )
        )
    ):
        raise OfflineContextBindingRejected("constructed context binding changed")



def bind_offline_context_request(
    request_id: str, preview: OfflineContextPreview,
) -> OfflineContextRequestBinding:
    """Revalidate a bounded v1 fixture preview; bind its digest to one request.

    This is a local integrity check only, not a replay ledger, authenticated
    identity, consent check, or permission to publish context content.
    """
    # Fixed-width ASCII identifiers and a bounded canonical JSON string are
    # rejected before regex scanning, UTF-8 allocation or private parsing.
    _assert_original_private_codec()
    if type(request_id) is not str or len(request_id) != 71
        or _REQUEST.fullmatch(request_id) is None:
        raise OfflineContextBindingRejected("exact local context request ID required")
    if type(preview) is not _PREVIEW_TYPE:
        raise OfflineContextBindingRejected("exact local context preview required")
    _assert_original_denials()
    pinned = (
        preview.owner_digest, preview.record_ids,
        preview.canonical_local_json, preview.local_digest,
    )
    preview_permissions = _PREVIEW_DENIALS
    binding_permissions = _BINDING_DENIALS
    preview_descriptors = _ORIGINAL_PREVIEW_DENIALS
    binding_descriptors = _ORIGINAL_BINDING_DENIALS

    def unchanged() -> None:
        _assert_original_denials()
        try:
            if (
                type(preview) is not _PREVIEW_TYPE
                or any(now is not old for now, old in zip((
                    preview.owner_digest, preview.record_ids,
                    preview.canonical_local_json, preview.local_digest,
                ), pinned, strict=True))
                or preview.consent_verified is not False
                or preview.external_export_authorized is not False
                or preview.tool_dispatch_authorized is not False
                or preview.retention_authorized is not False
            ):
                raise OfflineContextBindingRejected("context preview carrier changed")
            # The final False getter can still mutate the previously checked
            # source or an earlier permission descriptor. Check both again.
            if (
                any(
                    now is not old for now, old in zip((
                        preview.owner_digest, preview.record_ids,
                        preview.canonical_local_json, preview.local_digest,
                    ), pinned, strict=True)
                )
                or any(
                    vars(_PREVIEW_TYPE).get(name) is not original
                    for name, original in zip(
                        preview_permissions, preview_descriptors, strict=True,
                    )
                )
            ):
                raise OfflineContextBindingRejected("context preview carrier changed")
        except (AttributeError, TypeError, ValueError) as exc:
            if type(exc) is OfflineContextBindingRejected:
                raise
            raise OfflineContextBindingRejected("context preview carrier invalid") from exc

    unchanged()
    owner, ids, canonical, digest = pinned
    # Preserve the existing byte-budget diagnostic without allocating a
    # potentially huge UTF-8 buffer for an already oversized string.
    if type(canonical) is str and len(canonical) > 65_536:
        raise OfflineContextBindingRejected("context serialized byte budget exceeded")
    if (
        type(owner) is not str or len(owner) != 64
        or _SHA.fullmatch(owner) is None
        or type(ids) is not tuple or not 1 <= len(ids) <= 32
        or any(type(x) is not str or len(x) != 36
               or _RECORD.fullmatch(x) is None for x in ids)
        or ids != tuple(sorted(set(ids)))
        or type(canonical) is not str
        or type(digest) is not str or len(digest) != 64
        or _SHA.fullmatch(digest) is None
    ):
        raise OfflineContextBindingRejected("invalid context preview metadata")
    try:
        encoded = canonical.encode("utf-8", errors="strict")
        if len(encoded) > 65_536:
            raise OfflineContextBindingRejected("context serialized byte budget exceeded")
        _assert_original_private_codec()
        decoded = json.loads(canonical)
        _assert_original_private_codec()
        recanonical = json.dumps(
            decoded, sort_keys=True, ensure_ascii=True,
            allow_nan=False, separators=(",", ":"),
        )
        _assert_original_private_codec()
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as exc:
        if type(exc) is OfflineContextBindingRejected:
            raise
        raise OfflineContextBindingRejected("context preview JSON invalid") from exc
    unchanged()
    if (
        type(decoded) is not dict or set(decoded) != {"owner_digest", "records"}
        or decoded["owner_digest"] != owner
        or type(decoded["records"]) is not list
        or len(decoded["records"]) != len(ids)
        or canonical != recanonical
    ):
        raise OfflineContextBindingRejected("context preview JSON identity mismatch")
    total = 0
    for expected_id, record in zip(ids, decoded["records"], strict=True):
        if (
            type(record) is not dict
            or set(record) != {"record_id", "scope_digest", "content"}
            or type(record["record_id"]) is not str
            or len(record["record_id"]) != 36
            or record["record_id"] != expected_id
            or type(record["scope_digest"]) is not str
            or len(record["scope_digest"]) != 64
            or _SHA.fullmatch(record["scope_digest"]) is None
            or type(record["content"]) is not str
            or len(record["content"]) > 4096
        ):
            raise OfflineContextBindingRejected("context preview records changed")
        try:
            record_bytes = record["content"].encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise OfflineContextBindingRejected("context preview text invalid") from exc
        if len(record_bytes) > 4096:
            raise OfflineContextBindingRejected("context preview record budget exceeded")
        total += len(record_bytes)
        if total > 16384:
            raise OfflineContextBindingRejected("context preview total budget exceeded")
    unchanged()
    _assert_original_private_codec()
    if hashlib.sha256(_PREVIEW_DOMAIN + encoded).hexdigest() != digest:
        raise OfflineContextBindingRejected("context preview local digest mismatch")
    _assert_original_private_codec()
    bound_payload = json.dumps(
        (request_id, owner, ids, digest), separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    unchanged()
    _assert_original_private_codec()
    binding_digest = hashlib.sha256(_BINDING_DOMAIN + bound_payload).hexdigest()
    unchanged()
    result = OfflineContextRequestBinding(
        request_id, owner, digest, len(ids), binding_digest,
    )
    def stable_result() -> None:
        _assert_original_denials()
        # Preview permission getters and constructed-result permission getters
        # are reentrant callbacks. Neither may silently grant authority by
        # rebinding a previously checked descriptor or replacing its evidence.
        unchanged()
        if (
            type(result) is not _BINDING_TYPE
            or result.request_id is not request_id
            or result.owner_digest is not owner
            or result.context_digest is not digest
            or type(result.record_count) is not int
            or result.record_count != len(ids)
            or result.binding_digest is not binding_digest
            or any(
                vars(_BINDING_TYPE).get(name) is not original
                for name, original in zip(
                    binding_permissions, binding_descriptors, strict=True,
                )
            )
        ):
            raise OfflineContextBindingRejected("constructed context binding changed")

    stable_result()
    for authority in binding_permissions:
        if getattr(result, authority) is not False:
            raise OfflineContextBindingRejected("constructed context binding changed")
        stable_result()
    return result
