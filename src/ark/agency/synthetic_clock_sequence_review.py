"""Untrusted, disconnected clock-evidence continuity fixture.

All clock values and source identifiers are caller supplied. A local digest
chain and monotonic ordering are NOT a trusted clock, signed time proof,
human approval, or permission for external action. No OS clock is accessed.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

_MAX = 2**63 - 1
_LIMIT = 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CHAIN = re.compile(r"clk_[0-9a-f]{64}\Z")


def _hash(domain: str, fields: object) -> str:
    payload = json.dumps(
        fields, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "clk_" + hashlib.sha256(domain.encode() + b"\0" + payload).hexdigest()


_GENESIS = _hash("ARK-disconnected-clock-genesis-v1", ())
_EMPTY_FIELDS = (0, "", -1, -1, _GENESIS)


class SyntheticClockRejected(RuntimeError):
    """Caller-supplied timing evidence is malformed or discontinuous."""


@dataclass(frozen=True, slots=True)
class SyntheticClockSample:
    """One unauthenticated caller clock sample; sequence starts at 1."""

    seq: int
    source_digest: str
    wall_ms: int
    monotonic_ns: int


@dataclass(frozen=True, slots=True)
class SyntheticClockWitness:
    event_count: int
    source_digest: str
    last_wall_ms: int
    last_monotonic_ns: int
    chain_hash: str

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


EMPTY_CLOCK_WITNESS = SyntheticClockWitness(*_EMPTY_FIELDS)


def _fields(value: SyntheticClockWitness) -> tuple[object, ...]:
    return (
        value.event_count, value.source_digest, value.last_wall_ms,
        value.last_monotonic_ns, value.chain_hash,
    )


def _check_witness(value: SyntheticClockWitness) -> None:
    if (
        type(value.event_count) is not int
        or not 0 <= value.event_count <= _LIMIT
        or type(value.chain_hash) is not str
        or not _CHAIN.fullmatch(value.chain_hash)
        or value.trusted_clock_verified is not False
        or value.dispatch_authorized is not False
        or value.automatic_replay_authorized is not False
        or type(value.source_digest) is not str
        or (
            value.event_count == 0 and _fields(value) != _EMPTY_FIELDS
        )
        or (
            value.event_count > 0 and (
                not _DIGEST.fullmatch(value.source_digest)
                or type(value.last_wall_ms) is not int
                or type(value.last_monotonic_ns) is not int
                or not 0 <= value.last_wall_ms <= _MAX
                or not 0 <= value.last_monotonic_ns <= _MAX
            )
        )
    ):
        raise SyntheticClockRejected("invalid synthetic clock witness")


def review_synthetic_clock_sequence(
    samples: Iterable[SyntheticClockSample],
    *,
    retained: SyntheticClockWitness | None = None,
    max_samples: int = _LIMIT,
) -> SyntheticClockWitness:
    """Bounded, read-only replay from genesis with optional retained prefix.

    The full sequence must be supplied again when checking a retained prefix.
    Consecutive local samples cannot authenticate clock hardware or origin.
    """
    if type(max_samples) is not int or not 1 <= max_samples <= _LIMIT:
        raise SyntheticClockRejected("invalid clock sample budget")
    if retained is not None and type(retained) is not SyntheticClockWitness:
        raise SyntheticClockRejected("retained clock witness requires exact type")
    retained_epoch = _fields(retained) if retained is not None else None
    retained_carriers = _fields(retained) if retained is not None else None
    if retained is not None:
        _check_witness(retained)
        if (
            _fields(retained) != retained_epoch
            or any(
                actual is not original
                for actual, original in zip(
                    _fields(retained), retained_carriers, strict=True,
                )
            )
        ):
            raise SyntheticClockRejected("retained clock witness changed")
        if retained.event_count > max_samples:
            raise SyntheticClockRejected("retained clock history exceeds sample budget")

    observed: list[
        tuple[SyntheticClockSample, int, str, int, int]
    ] = []
    # Do not trust a caller-reflectively mutable exported singleton as replay
    # genesis. Each review starts from the module's fixed empty-field vector.
    result = SyntheticClockWitness(*_EMPTY_FIELDS)
    result_epoch = _fields(result)
    result_carriers = (result.source_digest, result.chain_hash)

    def assert_result_epoch() -> None:
        # The iterable may mutate the last locally constructed witness while
        # yielding its NEXT sample or finishing in generator finally. A frozen
        # dataclass alone does not protect its reflective result carriers.
        if (
            type(result) is not SyntheticClockWitness
            or _fields(result) != result_epoch
            or result.source_digest is not result_carriers[0]
            or result.chain_hash is not result_carriers[1]
            or result.trusted_clock_verified is not False
            or result.dispatch_authorized is not False
            or result.automatic_replay_authorized is not False
        ):
            raise SyntheticClockRejected("constructed clock witness changed during sequence")

    def assert_epoch() -> None:
        if retained is not None and (
            _fields(retained) != retained_epoch
            or any(
                actual is not original
                for actual, original in zip(
                    _fields(retained), retained_carriers, strict=True,
                )
            )
        ):
            raise SyntheticClockRejected("retained clock witness changed")
        for sample, seq, source, wall, mono in observed:
            if (
                type(sample) is not SyntheticClockSample
                or any(
                    actual is not original
                    for actual, original in zip(
                        (sample.seq, sample.source_digest,
                         sample.wall_ms, sample.monotonic_ns),
                        (seq, source, wall, mono), strict=True,
                    )
                )
                or (sample.seq, sample.source_digest, sample.wall_ms,
                    sample.monotonic_ns) != (seq, source, wall, mono)
            ):
                raise SyntheticClockRejected("prior clock sample changed")

    try:
        source_iterator = iter(samples)
        assert_epoch()
        for sample in source_iterator:
            assert_epoch()
            assert_result_epoch()
            if len(observed) >= max_samples:
                raise SyntheticClockRejected("clock sample budget exceeded")
            if type(sample) is not SyntheticClockSample:
                raise SyntheticClockRejected("exact synthetic clock sample required")
            epoch = (
                sample.seq, sample.source_digest, sample.wall_ms,
                sample.monotonic_ns,
            )
            seq, source, wall, mono = epoch
            if (
                type(seq) is not int or seq != result.event_count + 1
                or type(source) is not str or not _DIGEST.fullmatch(source)
                or type(wall) is not int or not 0 <= wall <= _MAX
                or type(mono) is not int or not 0 <= mono <= _MAX
                or result.event_count > 0 and (
                    source != result.source_digest
                    or wall < result.last_wall_ms
                    or mono <= result.last_monotonic_ns
                )
            ):
                raise SyntheticClockRejected(
                    "synthetic clock sequence, source or time regressed"
                )
            observed.append((sample, seq, source, wall, mono))
            # A digest or constructor callback must not alter the previous
            # link after it has been used in the chain. The sample/retained
            # witness checks above do not cover the locally built result.
            prior = result
            prior_fields = _fields(prior)
            prior_chain_carrier = prior.chain_hash
            next_hash = _hash(
                "ARK-disconnected-clock-event-v1",
                (seq, source, wall, mono, prior_chain_carrier),
            )
            assert_epoch()
            if (
                _fields(prior) != prior_fields
                or prior.chain_hash is not prior_chain_carrier
            ):
                raise SyntheticClockRejected("prior clock chain link changed")
            if type(next_hash) is not str or not _CHAIN.fullmatch(next_hash):
                raise SyntheticClockRejected("invalid synthetic clock event digest")
            candidate = SyntheticClockWitness(seq, source, wall, mono, next_hash)
            assert_epoch()
            if (
                _fields(prior) != prior_fields
                or prior.chain_hash is not prior_chain_carrier
                or type(candidate) is not SyntheticClockWitness
                or _fields(candidate) != (seq, source, wall, mono, next_hash)
                # A reentrant constructor may replace exact, equal-text
                # source/hash carriers while preserving the digest values.
                # Preserve the caller's source and freshly computed chain link
                # as the original witness objects, not merely their text.
                or candidate.event_count is not seq
                or candidate.source_digest is not source
                or candidate.last_wall_ms is not wall
                or candidate.last_monotonic_ns is not mono
                or candidate.chain_hash is not next_hash
                or candidate.trusted_clock_verified is not False
                or candidate.dispatch_authorized is not False
                or candidate.automatic_replay_authorized is not False
            ):
                raise SyntheticClockRejected("constructed clock chain link changed")
            result = candidate
            result_epoch = _fields(candidate)
            result_carriers = (candidate.source_digest, candidate.chain_hash)
            if retained is not None and seq == retained.event_count and result != retained:
                raise SyntheticClockRejected("retained clock prefix differs")
        # StopIteration/finally may rewrite either an earlier input sample
        # or the last constructed result after its digest has been checked.
        assert_epoch()
        assert_result_epoch()
        if not observed:
            raise SyntheticClockRejected("empty clock evidence is insufficient")
        if retained is not None and retained.event_count > result.event_count:
            raise SyntheticClockRejected("clock history shorter than retained witness")
        return result
    except (AttributeError, TypeError, ValueError) as exc:
        raise SyntheticClockRejected("malformed clock sample iterator") from exc
