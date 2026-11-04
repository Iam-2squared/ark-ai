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
_DOMAIN = b"ark:disconnected-observation-fixture-chain:v1\0"


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


def _assert_original_implementations() -> None:
    if (
        ObservationEnvelope is not _ORIGINAL_ENVELOPE
        or vars(_ORIGINAL_ENVELOPE).get("observation_id") is not _ORIGINAL_ID
        or DisconnectedObservationChainReview is not _RESULT
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
        or type(source_id) is not str or not source_id
        or type(privacy_scope) is not str or not privacy_scope
        or any(type(row) is not _ORIGINAL_ENVELOPE for row in envelopes)
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
