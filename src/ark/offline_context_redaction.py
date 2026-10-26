"""Strict, disconnected local fixture masking with independently pinned source.

Full-mask mode requires coverage of *every* source codepoint; partial mode
may reveal unmasked text and MUST NOT be exported or treated as anonymized.
This never opens personal Memory, authenticates consent or grants disclosure.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_LABEL = re.compile(r"[A-Z][A-Z0-9_]{0,19}\Z")
_DOMAIN = b"ARK-detached-local-context-redaction-v1\0"
_MAX_TEXT = 8_192
_MAX_SPANS = 64


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
    masked_text: str
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
    if (
        type(text) is not str or not text or len(text) > _MAX_TEXT
        or type(owner_digest) is not str or _SHA.fullmatch(owner_digest) is None
        or type(scope_digest) is not str or _SHA.fullmatch(scope_digest) is None
        or type(retained_source_sha256) is not str
        or _SHA.fullmatch(retained_source_sha256) is None
        or type(spans) is not tuple or not 1 <= len(spans) <= _MAX_SPANS
        or any(type(span) is not OfflineRedactionSpan for span in spans)
        or type(require_complete) is not bool
    ):
        raise OfflineRedactionRejected("invalid redaction fixture or identity")
    roots = (
        text, owner_digest, scope_digest, retained_source_sha256,
        spans, require_complete,
    )
    originals = tuple(spans)
    pinned = tuple((s.start, s.end, s.label) for s in originals)

    def assert_epoch() -> None:
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
            or type(label) is not str or _LABEL.fullmatch(label) is None
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
    serialized = json.dumps(
        {"owner": owner_digest, "scope": scope_digest, "source": observed,
         "mask": index, "complete": require_complete, "result": result_text},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    )
    digest = hashlib.sha256(_DOMAIN + serialized.encode("ascii")).hexdigest()
    assert_epoch()
    result = RedactedOfflinePreview(
        owner_digest, scope_digest, observed, result_text, masked,
        require_complete, digest,
    )
    assert_epoch()
    if (
        result.owner_digest is not owner_digest
        or result.scope_digest is not scope_digest
        or result.source_sha256 is not observed
        or result.masked_text is not result_text
        or result.masked_characters != masked
        or result.complete_masking is not require_complete
        or result.local_digest is not digest
    ):
        raise OfflineRedactionRejected("masked preview construction mutated")
    return result
