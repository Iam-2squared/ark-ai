"""Strict, disconnected local fixture masking with independently pinned source.

Full-mask mode requires coverage of *every* source codepoint; partial mode
may reveal unmasked text and MUST NOT be exported or treated as anonymized.
This never opens personal Memory, authenticates consent or grants disclosure.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_LABEL = re.compile(r"[A-Z][A-Z0-9_]{0,19}\Z")
_DOMAIN = b"ARK-detached-local-context-redaction-v1\0"
_MAX_TEXT = 8_192
_MAX_SPANS = 64
# These lexical grammars, budgets and hash-domain bytes are part of the
# privacy review. A replaced matcher or budget must not inspect private text
# or silently widen what reaches a digest/preview.
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_LABEL_PATTERN = _LABEL
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_TEXT = _MAX_TEXT
_ORIGINAL_MAX_SPANS = _MAX_SPANS
# Reject a replaced SHA-256 callback BEFORE handing private fixture bytes
# to it, even when a valid source digest was independently supplied.
_ORIGINAL_SHA256 = hashlib.sha256
# Pin canonical JSON encoding at import; digesting injected JSON is not proof
# that the reviewed owner/scope and masked result actually reached the digest.
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_JSON_LOADS = json.loads


class OfflineRedactionRejected(ValueError):
    """Text, source evidence or masking boundaries are unsafe or altered."""


@dataclass(frozen=True, slots=True)
class OfflineRedactionSpan:
    start: int
    end: int
    label: str


@dataclass(frozen=True, slots=True)
class RedactedOfflinePreview:
    owner_digest: str
    scope_digest: str
    source_sha256: str
    masked_text: str = field(repr=False)
    masked_characters: int
    complete_masking: bool
    local_digest: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def privacy_erasure_proven(self) -> bool:
        return False

    @property
    def external_export_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False


_REDACTED_RESULT_TYPE = RedactedOfflinePreview
_REDACTION_SPAN_TYPE = OfflineRedactionSpan
_SPAN_FIELDS = ("start", "end", "label")
_RESULT_FIELDS = (
    "owner_digest", "scope_digest", "source_sha256", "masked_text",
    "masked_characters", "complete_masking", "local_digest",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SPAN_FIELDS = tuple(vars(_REDACTION_SPAN_TYPE)[name] for name in _SPAN_FIELDS)
_ORIGINAL_RESULT_FIELDS = tuple(vars(_REDACTED_RESULT_TYPE)[name] for name in _RESULT_FIELDS)
_ORIGINAL_SPAN_HOOKS = tuple(
    vars(_REDACTION_SPAN_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_REDACTED_RESULT_TYPE).get(name) for name in _CARRIER_HOOKS
)
_DENIAL_NAMES = (
    "consent_verified", "privacy_erasure_proven",
    "external_export_authorized", "tool_dispatch_authorized",
)
_ORIGINAL_DENIAL_DESCRIPTORS = tuple(
    vars(_REDACTED_RESULT_TYPE)[name] for name in _DENIAL_NAMES
)


def _require_original_denials() -> None:
    # A hostile descriptor may pretend to be the original when read through
    # its class, while running arbitrary code as a side effect. Inspect the
    # static class dictionary instead of invoking the replacement __get__.
    if (
        RedactedOfflinePreview is not _REDACTED_RESULT_TYPE
        or OfflineRedactionSpan is not _REDACTION_SPAN_TYPE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _LABEL is not _ORIGINAL_LABEL_PATTERN
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or type(_MAX_TEXT) is not int or _MAX_TEXT != _ORIGINAL_MAX_TEXT
        or type(_MAX_SPANS) is not int or _MAX_SPANS != _ORIGINAL_MAX_SPANS
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or json.loads is not _ORIGINAL_JSON_LOADS
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in (
                (_REDACTION_SPAN_TYPE, _SPAN_FIELDS, _ORIGINAL_SPAN_FIELDS),
                (_REDACTED_RESULT_TYPE, _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or any(
            vars(cls).get(name) is not original
            for cls, originals in (
                (_REDACTION_SPAN_TYPE, _ORIGINAL_SPAN_HOOKS),
                (_REDACTED_RESULT_TYPE, _ORIGINAL_RESULT_HOOKS),
            )
            for name, original in zip(_CARRIER_HOOKS, originals, strict=True)
        )
        or any(
            vars(_REDACTED_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise OfflineRedactionRejected(
            "masked preview authority definition changed"
        )


def preview_offline_redaction(
    text: str,
    *,
    owner_digest: str,
    scope_digest: str,
    retained_source_sha256: str,
    spans: tuple[OfflineRedactionSpan, ...],
    require_complete: bool = True,
) -> RedactedOfflinePreview:
    """Mask explicitly supplied synthetic text, returning only local preview.

    The source digest must have been retained independently; it is not an
    authentication signature. Labels and boundaries are *caller supplied*, not
    automated PII detection. Even complete coverage conveys no export consent.
    """
    # Reject a substitute matcher/grammar BEFORE it can evaluate even the
    # owner/scope digest. The later epoch checks also cover callback drift.
    _require_original_denials()
    if (
        type(text) is not str or not text or len(text) > _MAX_TEXT
        or type(owner_digest) is not str or len(owner_digest) != 64
        or _SHA.fullmatch(owner_digest) is None
        or type(scope_digest) is not str or len(scope_digest) != 64
        or _SHA.fullmatch(scope_digest) is None
        or type(retained_source_sha256) is not str
        or len(retained_source_sha256) != 64
        or _SHA.fullmatch(retained_source_sha256) is None
        or type(spans) is not tuple or not 1 <= len(spans) <= _MAX_SPANS
        or any(type(span) is not OfflineRedactionSpan for span in spans)
        or type(require_complete) is not bool
    ):
        raise OfflineRedactionRejected("invalid redaction fixture or identity")
    # Before touching even synthetic private source bytes, reject a
    # substituted denial getter, including an always-False callback.
    # Re-check around all subsequent callbacks instead of re-baselining.
    _require_original_denials()
    roots = (
        text, owner_digest, scope_digest, retained_source_sha256,
        spans, require_complete,
    )
    originals = tuple(spans)
    pinned = tuple((s.start, s.end, s.label) for s in originals)

    def assert_epoch() -> None:
        _require_original_denials()
        if (
            any(actual is not original for actual, original in zip(
                (text, owner_digest, scope_digest, retained_source_sha256,
                 spans, require_complete), roots, strict=True,
            ))
            or any(spans[i] is not row or any(now is not old for now, old in zip(
                (row.start, row.end, row.label), fields, strict=True,
            )) for i, (row, fields) in enumerate(zip(originals, pinned, strict=True)))
        ):
            raise OfflineRedactionRejected("redaction fixture changed during review")

    assert_epoch()
    try:
        original_bytes = text.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise OfflineRedactionRejected("invalid source Unicode") from exc
    if len(original_bytes) > _MAX_TEXT:
        raise OfflineRedactionRejected("source byte budget exceeded")
    observed = hashlib.sha256(original_bytes).hexdigest()
    assert_epoch()
    if observed != retained_source_sha256:
        raise OfflineRedactionRejected("source does not match independently retained digest")

    cursor = 0
    masked = 0
    output: list[str] = []
    index: list[tuple[int, int, str]] = []
    for _row, (start, end, label) in zip(originals, pinned, strict=True):
        assert_epoch()
        if (
            type(start) is not int or type(end) is not int
            or not 0 <= cursor <= start < end <= len(text)
            or type(label) is not str or len(label) > 20
            or _LABEL.fullmatch(label) is None
            or (require_complete and cursor != start)
        ):
            raise OfflineRedactionRejected("invalid, overlapping or uncovered redaction span")
        output.append(text[cursor:start])
        output.append(f"[MASK:{label}]")
        index.append((start, end, label))
        masked += end - start
        cursor = end
    if require_complete and cursor != len(text):
        raise OfflineRedactionRejected("complete masking left trailing source text")
    output.append(text[cursor:])
    result_text = "".join(output)
    if len(result_text.encode("utf-8")) > 16_384:
        raise OfflineRedactionRejected("masked preview budget exceeded")
    assert_epoch()
    expected_payload = {
        "owner": owner_digest, "scope": scope_digest, "source": observed,
        "mask": [list(item) for item in index],
        "complete": require_complete, "result": result_text,
    }
    serialized = json.dumps(
        expected_payload,
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    )
    assert_epoch()
    # A substituted serializer can emit plausible JSON that describes a
    # different private source, owner or masking boundary. Round-trip the
    # exact expected object and compare with import-pinned canonical bytes
    # BEFORE using it as digest evidence. No raw source is logged.
    try:
        if type(serialized) is not str:
            raise ValueError("non-string serializer output")
        decoded = json.loads(serialized)
        canonical = _ORIGINAL_JSON_DUMPS(
            expected_payload, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"),
        )
        encoded = serialized.encode("ascii", errors="strict")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise OfflineRedactionRejected(
            "masked preview serialization invalid"
        ) from exc
    assert_epoch()
    if decoded != expected_payload or serialized != canonical:
        raise OfflineRedactionRejected(
            "masked preview serialization differs from reviewed source"
        )
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    assert_epoch()
    result = RedactedOfflinePreview(
        owner_digest, scope_digest, observed, result_text, masked,
        require_complete, digest,
    )
    assert_epoch()
    if (
        type(result) is not _REDACTED_RESULT_TYPE
        or result.owner_digest is not owner_digest
        or result.scope_digest is not scope_digest
        or result.source_sha256 is not observed
        or result.masked_text is not result_text
        or type(result.masked_characters) is not int
        or result.masked_characters != masked
        or type(result.complete_masking) is not bool
        or result.complete_masking is not require_complete
        or result.local_digest is not digest
        # A local masking receipt is not consent, erasure, an export
        # authorization, or a ToolBackend execution grant.
        or result.consent_verified is not False
        or result.privacy_erasure_proven is not False
        or result.external_export_authorized is not False
        or result.tool_dispatch_authorized is not False
    ):
        raise OfflineRedactionRejected("masked preview construction mutated")
    assert_epoch()
    # Denial-only authority properties are callback boundaries. A getter
    # returning False may still reflectively replace a frozen result field.
    # Revalidate the exact output after the LAST property read, not just the
    # unchanged caller input. The masked text must remain the reviewed bytes.
    if (
        type(result) is not _REDACTED_RESULT_TYPE
        or result.owner_digest is not owner_digest
        or result.scope_digest is not scope_digest
        or result.source_sha256 is not observed
        or result.masked_text is not result_text
        or type(result.masked_characters) is not int
        or result.masked_characters != masked
        or type(result.complete_masking) is not bool
        or result.complete_masking is not require_complete
        or result.local_digest is not digest
        or any(
            vars(_REDACTED_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise OfflineRedactionRejected(
            "masked preview changed after authority review"
        )
    assert_epoch()
    return result
