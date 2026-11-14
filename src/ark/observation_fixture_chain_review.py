"""Closed, disconnected lineage review for caller-supplied observation fixtures.

This optional reviewer does not acquire, persist, retain, or disclose media.
It proves only in-memory structural consistency of a *closed* synthetic chain:
the first envelope has no parent, each subsequent envelope names the
immediately previous content digest, and content digests are unique so parent
references are unambiguous. Other DAGs are not rejected by the
underlying ObservationEnvelope contract; they are outside this review mode.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .observations import ObservationEnvelope

_MAX_ENVELOPES = 256
_ORIGINAL_ENVELOPE = ObservationEnvelope
_ORIGINAL_VALIDATE = ObservationEnvelope.__post_init__
_ORIGINAL_ID = vars(ObservationEnvelope)["observation_id"]
# A frozen envelope can have its slot or lookup descriptors replaced before
# the first private fixture read. Reject those substitutions without calling
# their getters or validators.
_ENVELOPE_FIELDS = (
    "kind", "source_id", "adapter_id", "privacy_scope",
    "ingested_at_ms", "content_sha256", "parent_sha256", "schema_version",
)
_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_ENVELOPE_FIELDS = tuple(
    vars(_ORIGINAL_ENVELOPE)[name] for name in _ENVELOPE_FIELDS
)
_ORIGINAL_ENVELOPE_HOOKS = tuple(
    vars(_ORIGINAL_ENVELOPE).get(name) for name in _HOOKS
)
_DOMAIN = b"ark:disconnected-observation-fixture-chain:v1\0"
# Private fixture identity and final digest must use the import-time hash
# implementation and a byte-identical *object*, not a caller replacement.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DOMAIN = _DOMAIN
# Protocol sizes, label/order vectors and validation hooks are just as
# security-sensitive as the hash implementation. Pin their original carriers
# before reading any caller-supplied private observation fixture.
_ORIGINAL_MAX_ENVELOPES = _MAX_ENVELOPES
_ORIGINAL_ENVELOPE_FIELDS_VECTOR = _ENVELOPE_FIELDS
_ORIGINAL_HOOKS_VECTOR = _HOOKS


class ObservationFixtureChainRejected(ValueError):
    """The offline fixture chain cannot be trusted as a closed review input."""


@dataclass(frozen=True, slots=True)
class DisconnectedObservationChainReview:
    source_id: str
    privacy_scope: str
    envelope_count: int
    first_observation_id: str
    last_observation_id: str
    chain_sha256: str

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


_RESULT = DisconnectedObservationChainReview
_DENIALS = (
    "source_authenticated", "consent_verified", "dispatch_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[name] for name in _DENIALS)
_RESULT_FIELDS = (
    "source_id", "privacy_scope", "envelope_count",
    "first_observation_id", "last_observation_id", "chain_sha256",
)
_ORIGINAL_RESULT_INIT = vars(_RESULT)["__init__"]
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT)[name] for name in _RESULT_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(vars(_RESULT).get(name) for name in _HOOKS)
_ORIGINAL_RESULT_FIELDS_VECTOR = _RESULT_FIELDS
_ORIGINAL_DENIALS_VECTOR = _DENIALS


def _assert_original_implementations() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or type(_MAX_ENVELOPES) is not int
        or _MAX_ENVELOPES != _ORIGINAL_MAX_ENVELOPES
        or _ENVELOPE_FIELDS is not _ORIGINAL_ENVELOPE_FIELDS_VECTOR
        or _HOOKS is not _ORIGINAL_HOOKS_VECTOR
        or _RESULT_FIELDS is not _ORIGINAL_RESULT_FIELDS_VECTOR
        or _DENIALS is not _ORIGINAL_DENIALS_VECTOR
    ):
        raise ObservationFixtureChainRejected(
            "disconnected fixture review digest implementation changed"
        )
    if (
        ObservationEnvelope is not _ORIGINAL_ENVELOPE
        or vars(_ORIGINAL_ENVELOPE).get("observation_id") is not _ORIGINAL_ID
        or vars(_ORIGINAL_ENVELOPE).get("__post_init__") is not _ORIGINAL_VALIDATE
        or any(
            vars(_ORIGINAL_ENVELOPE).get(name) is not original
            for name, original in zip(
                _ENVELOPE_FIELDS, _ORIGINAL_ENVELOPE_FIELDS, strict=True,
            )
        )
        or any(
            vars(_ORIGINAL_ENVELOPE).get(name) is not original
            for name, original in zip(_HOOKS, _ORIGINAL_ENVELOPE_HOOKS, strict=True)
        )
        or DisconnectedObservationChainReview is not _RESULT
        or vars(_RESULT).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(
                _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_HOOKS, _ORIGINAL_RESULT_HOOKS, strict=True)
        )
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise ObservationFixtureChainRejected(
            "disconnected fixture review implementation changed"
        )


def review_disconnected_fixture_chain(
    envelopes: tuple[ObservationEnvelope, ...],
    *,
    source_id: str,
    privacy_scope: str,
) -> DisconnectedObservationChainReview:
    """Return a digest-only, deny-only review of a closed synthetic chain.

    No trusted capture clock, source authentication, consent or tool approval
    is inferred from this local review. The digest is not a durable anchor.
    """
    _assert_original_implementations()
    if (
        type(envelopes) is not tuple
        or not 1 <= len(envelopes) <= _MAX_ENVELOPES
        or type(source_id) is not str or not source_id.strip()
        or len(source_id) > 1024
        or type(privacy_scope) is not str or not privacy_scope.strip()
        or len(privacy_scope) > 1024
        or any(type(row) is not _ORIGINAL_ENVELOPE for row in envelopes)
    ):
        raise ObservationFixtureChainRejected("exact bounded fixture chain required")
    # These caller-supplied labels are encoded into the final digest. Reject
    # non-UTF-8 surrogate text before iterating potentially private fixture
    # fields or invoking envelope identity/validation callbacks.
    try:
        encoded_source = source_id.encode("utf-8")
        encoded_privacy = privacy_scope.encode("utf-8")
    except UnicodeError as exc:
        raise ObservationFixtureChainRejected(
            "fixture chain labels must be valid UTF-8"
        ) from exc
    # Request labels cross the same digest boundary as envelope labels. Limit
    # encoded bytes BEFORE reading any private fixture fields: 1024 Unicode
    # codepoints can occupy 4096 bytes of serialized UTF-8.
    # The v1 chain digest uses NUL-delimited source/scope labels:
    # DOMAIN + source + NUL + privacy + NUL + observation IDs.
    # An embedded NUL makes the prefix framing ambiguous. The underlying
    # ObservationEnvelope may represent it, but this optional stricter
    # closed-chain review does not accept ambiguous provenance labels.
    if (
        len(encoded_source) > 1024 or len(encoded_privacy) > 1024
        or b"\x00" in encoded_source or b"\x00" in encoded_privacy
    ):
        raise ObservationFixtureChainRejected("exact bounded fixture chain required")

    fields = tuple((
        row.kind, row.source_id, row.adapter_id, row.privacy_scope,
        row.ingested_at_ms, row.content_sha256, row.parent_sha256,
        row.schema_version,
    ) for row in envelopes)
    originals = tuple(envelopes)

    def assert_epoch() -> None:
        _assert_original_implementations()
        try:
            stable = (
                type(envelopes) is tuple
                and len(envelopes) == len(originals)
                and all(
                    type(row) is _ORIGINAL_ENVELOPE
                    and row is original
                    and all(
                        current is initial
                        for current, initial in zip(
                            (
                                row.kind, row.source_id, row.adapter_id,
                                row.privacy_scope, row.ingested_at_ms,
                                row.content_sha256, row.parent_sha256,
                                row.schema_version,
                            ),
                            witness, strict=True,
                        )
                    )
                    for row, original, witness in zip(
                        envelopes, originals, fields, strict=True,
                    )
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise ObservationFixtureChainRejected(
                "fixture chain changed during review"
            ) from exc
        if not stable:
            raise ObservationFixtureChainRejected(
                "fixture chain changed during review"
            )

    observation_ids: list[str] = []
    seen_digests: set[str] = set()
    previous_digest: str | None = None
    previous_ms = -1
    for row, witness in zip(envelopes, fields, strict=True):
        assert_epoch()
        _ORIGINAL_VALIDATE(row)
        assert_epoch()
        (
            _, observed_source, _, observed_scope, observed_ms,
            digest, parent, _,
        ) = witness
        if (
            observed_source != source_id
            or observed_scope != privacy_scope
            or parent != previous_digest
            or observed_ms <= previous_ms
        ):
            raise ObservationFixtureChainRejected(
                "fixture chain provenance, parent or chronology mismatch"
            )
        # Each digest must resolve to precisely one position in the closed
        # linear chain. Repeated content digests would make a later parent
        # reference ambiguous (and can form a content-hash self-cycle).
        if digest in seen_digests:
            raise ObservationFixtureChainRejected(
                "fixture chain repeats a content digest"
            )
        seen_digests.add(digest)
        identity = _ORIGINAL_ID.fget(row)
        assert_epoch()
        if type(identity) is not str or not identity.startswith("obs_"):
            raise ObservationFixtureChainRejected("invalid observation identity")
        observation_ids.append(identity)
        previous_digest = digest
        previous_ms = observed_ms

    assert_epoch()
    encoded = "\n".join(observation_ids).encode("ascii")
    chain_sha = hashlib.sha256(
        _DOMAIN + source_id.encode("utf-8") + b"\0"
        + privacy_scope.encode("utf-8") + b"\0" + encoded
    ).hexdigest()
    assert_epoch()
    # Expected output is derived from validated INPUTS, never read back from
    # a reflected-mutable constructor result. Otherwise a constructor hook
    # can quietly rebase all later comparisons onto forged output values.
    expected = (
        source_id, privacy_scope, len(envelopes),
        observation_ids[0], observation_ids[-1], chain_sha,
    )
    result = _RESULT(*expected)

    def assert_result_epoch() -> None:
        if type(result) is not _RESULT or any(
            type(now) is not type(original)
            or now != original
            or now is not original
            for now, original in zip((
                result.source_id, result.privacy_scope, result.envelope_count,
                result.first_observation_id, result.last_observation_id,
                result.chain_sha256,
            ), expected, strict=True)
        ):
            raise ObservationFixtureChainRejected("fixture review result changed")

    assert_epoch()
    assert_result_epoch()
    for denial in _DENIALS:
        assert_epoch()
        assert_result_epoch()
        # The preceding result-field inspection may invoke a reflected
        # callback. Recheck the original descriptor immediately before the
        # first potentially executable authority getter.
        _assert_original_implementations()
        if getattr(result, denial) is not False:
            raise ObservationFixtureChainRejected("fixture review gained authority")
        # A getter can modify the descriptor of a later or earlier flag.
        _assert_original_implementations()
        assert_result_epoch()
    assert_epoch()
    assert_result_epoch()
    _assert_original_implementations()
    return result
