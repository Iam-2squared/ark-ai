"""Disconnected observation parent-lineage guard over metadata-only fixtures.

A content hash is not a signature, provenance proof or verified media source.
No hardware capture, processing of raw media, notification or ToolBackend
operation is permitted by this isolated reviewer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .observation_window_review import ObservationWindowReview
from .observations import ObservationEnvelope

# Preserve the import-time digest implementation for privacy metadata.
# Monkeypatches can otherwise forge local lineage digests or execute callbacks
# while the reviewer holds private envelope identifiers. This is only an
# in-process fail-closed guard, not authenticated provenance or a sandbox.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_LINEAGE_DOMAIN = b"ARK-observation-lineage-v1\0"
_ORIGINAL_LINEAGE_DOMAIN = _LINEAGE_DOMAIN


class SyntheticObservationLineageRejected(RuntimeError):
    """The fixture's claimed parent-chain identity is inconsistent."""


@dataclass(frozen=True, slots=True)
class SyntheticObservationLineageWitness:
    privacy_scope: str
    checked_at_ms: int
    observation_count: int
    lineage_digest: str

    @property
    def media_capture_authorized(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


_LINEAGE_RESULT_TYPE = SyntheticObservationLineageWitness
_LINEAGE_FIELDS = (
    "privacy_scope", "checked_at_ms", "observation_count", "lineage_digest",
)
_LINEAGE_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_LINEAGE_DENIALS = (
    "media_capture_authorized", "disclosure_authorized", "dispatch_authorized",
)
_ORIGINAL_LINEAGE_FIELDS = tuple(
    vars(_LINEAGE_RESULT_TYPE)[name] for name in _LINEAGE_FIELDS
)
_ORIGINAL_LINEAGE_HOOKS = tuple(
    vars(_LINEAGE_RESULT_TYPE).get(name) for name in _LINEAGE_HOOKS
)
_ORIGINAL_LINEAGE_DENIALS = tuple(
    vars(_LINEAGE_RESULT_TYPE)[name] for name in _LINEAGE_DENIALS
)


def _assert_original_lineage_result() -> None:
    # A slotted frozen witness is still mutable at its class definition.
    # Fail before calling a replaced constructor/field/False-only getter:
    # otherwise malicious fixture code could read privacy metadata before
    # the eventual result-shape or authority check rejects the result.
    if (
        SyntheticObservationLineageWitness is not _LINEAGE_RESULT_TYPE
        or any(
            vars(_LINEAGE_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _LINEAGE_FIELDS, _ORIGINAL_LINEAGE_FIELDS, strict=True,
            )
        )
        or any(
            vars(_LINEAGE_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _LINEAGE_HOOKS, _ORIGINAL_LINEAGE_HOOKS, strict=True,
            )
        )
        or any(
            vars(_LINEAGE_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _LINEAGE_DENIALS, _ORIGINAL_LINEAGE_DENIALS, strict=True,
            )
        )
    ):
        raise SyntheticObservationLineageRejected(
            "observation lineage result changed: authority definition modified"
        )


def _assert_original_digest_implementation() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _LINEAGE_DOMAIN is not _ORIGINAL_LINEAGE_DOMAIN
    ):
        raise SyntheticObservationLineageRejected(
            "observation lineage digest implementation changed"
        )


def review_synthetic_observation_lineage(
    envelopes: tuple[ObservationEnvelope, ...],
    *,
    privacy_scope: str,
    now_ms: int,
    max_age_ms: int,
) -> SyntheticObservationLineageWitness:
    """Validate resolved parent hashes, privacy and per-source chronology.

    Every parent must occur exactly once in the supplied local window.
    Matching hashes alone are never trusted if the parent is ambiguous.
    The result is an inert, content-free deterministic review witness.
    """
    if type(envelopes) is not tuple:
        raise SyntheticObservationLineageRejected("exact observation tuple required")
    _assert_original_lineage_result()
    _assert_original_digest_implementation()
    # Existing window construction enforces bounded membership, same privacy
    # scope, canonical envelope identity, age and caller-clock constraints.
    window = ObservationWindowReview(
        privacy_scope, now_ms, max_age_ms, envelopes,
    )
    window.assert_fresh_at(now_ms)
    # The initial window validates values, but later ID/hash callbacks can
    # reflectively replace equal-valued scalar carriers or temporarily change
    # a parent before restoring it at the final freshness check. Keep the
    # caller's exact original metadata epoch through graph construction.
    field_names = (
        "kind", "source_id", "adapter_id", "privacy_scope",
        "ingested_at_ms", "content_sha256", "parent_sha256",
        "schema_version",
    )
    epoch = tuple((envelope, tuple(
        getattr(envelope, name) for name in field_names
    )) for envelope in envelopes)

    def assert_epoch() -> None:
        _assert_original_digest_implementation()
        try:
            if any(
                any(getattr(item, name) is not original
                    for name, original in zip(field_names, values, strict=True))
                for item, values in epoch
            ):
                raise SyntheticObservationLineageRejected(
                    "observation lineage input epoch changed"
                )
            window.assert_fresh_at(now_ms)
        except (ValueError, TypeError, AttributeError) as exc:
            raise SyntheticObservationLineageRejected(
                "observation lineage input epoch changed"
            ) from exc

    by_content: dict[str, list[ObservationEnvelope]] = {}
    for envelope in envelopes:
        assert_epoch()
        by_content.setdefault(envelope.content_sha256, []).append(envelope)
    assert_epoch()

    parents: dict[str, str | None] = {}
    for envelope in envelopes:
        assert_epoch()
        parent_id = None
        if envelope.parent_sha256 is not None:
            options = by_content.get(envelope.parent_sha256, [])
            if not options:
                raise SyntheticObservationLineageRejected(
                    "observation parent hash is unresolved"
                )
            if len(options) != 1:
                raise SyntheticObservationLineageRejected(
                    "observation parent digest is ambiguous"
                )
            parent = options[0]
            if parent.source_id != envelope.source_id:
                raise SyntheticObservationLineageRejected(
                    "observation parent crosses source boundary"
                )
            if parent.ingested_at_ms > envelope.ingested_at_ms:
                raise SyntheticObservationLineageRejected(
                    "observation parent timestamp is after child"
                )
            parent_id = parent.observation_id
        parents[envelope.observation_id] = parent_id
        assert_epoch()

    completed: set[str] = set()
    for start in parents:
        current: str | None = start
        seen: set[str] = set()
        while current is not None and current not in completed:
            if current in seen:
                raise SyntheticObservationLineageRejected(
                    "observation parent-chain cycle detected"
                )
            seen.add(current)
            current = parents[current]
        completed.update(seen)

    assert_epoch()
    edges = tuple(sorted(parents.items()))
    payload = json.dumps(
        (1, privacy_scope, now_ms, max_age_ms, edges),
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    assert_epoch()
    digest = "olineage_" + hashlib.sha256(
        _LINEAGE_DOMAIN + payload
    ).hexdigest()
    # The cached window detects reflected changes to envelope metadata while
    # walking the graph. This does not attest source authenticity.
    assert_epoch()
    _assert_original_lineage_result()
    result = SyntheticObservationLineageWitness(
        privacy_scope, now_ms, len(envelopes), digest,
    )
    _assert_original_lineage_result()
    assert_epoch()
    if (
        type(result) is not _LINEAGE_RESULT_TYPE
        or result.privacy_scope is not privacy_scope
        or result.checked_at_ms is not now_ms
        or result.observation_count != len(envelopes)
        or result.lineage_digest is not digest
        # A real DTO with reflected property changes is just as unsafe as an
        # injected lookalike. Local lineage evidence never grants access.
        or result.media_capture_authorized is not False
        or result.disclosure_authorized is not False
        or result.dispatch_authorized is not False
    ):
        raise SyntheticObservationLineageRejected(
            "observation lineage result changed during construction"
        )
    # Denial-property getters are callbacks. A reflected getter may return
    # False while rewriting the result or any original observation after the
    # preceding epoch check. No post-denial mixed epoch may escape.
    assert_epoch()
    if (
        type(result) is not _LINEAGE_RESULT_TYPE
        or result.privacy_scope is not privacy_scope
        or result.checked_at_ms is not now_ms
        or type(result.observation_count) is not int
        or result.observation_count != len(envelopes)
        or result.lineage_digest is not digest
    ):
        raise SyntheticObservationLineageRejected(
            "observation lineage result changed after authority review"
        )
    assert_epoch()
    if (
        type(result) is not _LINEAGE_RESULT_TYPE
        or result.privacy_scope is not privacy_scope
        or result.checked_at_ms is not now_ms
        or result.observation_count != len(envelopes)
        or result.lineage_digest is not digest
    ):
        raise SyntheticObservationLineageRejected(
            "observation lineage result changed during final epoch check"
        )
    # A False-valued final denial getter may replace an EARLIER denial
    # descriptor after the first pass. Re-read each denial in order, then
    # recheck the original input epoch and immutable output after every
    # callback. This is a local synthetic guard, not consent or authority.
    for authority_name in _LINEAGE_DENIALS:
        _assert_original_lineage_result()
        if getattr(result, authority_name) is not False:
            raise SyntheticObservationLineageRejected(
                "observation lineage result gained authority after denial"
            )
        _assert_original_lineage_result()
        assert_epoch()
        if (
            type(result) is not _LINEAGE_RESULT_TYPE
            or result.privacy_scope is not privacy_scope
            or result.checked_at_ms is not now_ms
            or type(result.observation_count) is not int
            or result.observation_count != len(envelopes)
            or result.lineage_digest is not digest
        ):
            raise SyntheticObservationLineageRejected(
                "observation lineage result changed after denial"
            )
    _assert_original_lineage_result()
    assert_epoch()
    _assert_original_digest_implementation()
    return result
