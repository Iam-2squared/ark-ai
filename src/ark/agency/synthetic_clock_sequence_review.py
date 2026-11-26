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
# Import-original digest identity: a synthetic clock chain cannot rely on
# a substituted SHA/JSON implementation or a value-equal genesis carrier.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
# A changed local digest helper is executable code, even when hashlib and
# json remain original. Pin the function before any caller iterator is read.
_ORIGINAL_HASH_HELPER = _hash
_ORIGINAL_GENESIS = _GENESIS


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

_DENIAL_NAMES = (
    "trusted_clock_verified", "dispatch_authorized",
    "automatic_replay_authorized",
)
# Resolve class properties without running a descriptor's __get__.  A
# replacement can return the original property when accessed on the class,
# while doing arbitrary work if the descriptor is invoked.
_SAMPLE_TYPE = SyntheticClockSample
_WITNESS_TYPE = SyntheticClockWitness
_SAMPLE_FIELDS = ("seq", "source_digest", "wall_ms", "monotonic_ns")
_WITNESS_FIELDS = (
    "event_count", "source_digest", "last_wall_ms",
    "last_monotonic_ns", "chain_hash",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SAMPLE_FIELDS = tuple(
    vars(_SAMPLE_TYPE)[name] for name in _SAMPLE_FIELDS
)
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_SAMPLE_HOOKS = tuple(
    vars(_SAMPLE_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_DENIALS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _DENIAL_NAMES
)


# Keep parser/size constraints as exact import-time protocol witnesses too.
# Changed bounds can otherwise affect iterator admission BEFORE any digest
# round-trip, even when SHA/JSON and all result constructors remain original.
_ORIGINAL_DIGEST_PATTERN = _DIGEST
_ORIGINAL_CHAIN_PATTERN = _CHAIN
_ORIGINAL_MAX_MS = _MAX
_ORIGINAL_SAMPLE_LIMIT = _LIMIT
_ORIGINAL_EMPTY_FIELDS = _EMPTY_FIELDS
_ORIGINAL_DENIAL_NAMES = _DENIAL_NAMES


def _denials_original() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or _hash is not _ORIGINAL_HASH_HELPER
        or _GENESIS is not _ORIGINAL_GENESIS
        or _DIGEST is not _ORIGINAL_DIGEST_PATTERN
        or _CHAIN is not _ORIGINAL_CHAIN_PATTERN
        # Numeric subclasses can compare equal while running arbitrary
        # __eq__/__ne__ code on a caller-controlled clock evidence path.
        # Refuse them before checking equality or consuming the iterator.
        or type(_MAX) is not int
        or type(_LIMIT) is not int
        or _MAX != _ORIGINAL_MAX_MS
        or _LIMIT != _ORIGINAL_SAMPLE_LIMIT
        or _EMPTY_FIELDS is not _ORIGINAL_EMPTY_FIELDS
        or _DENIAL_NAMES is not _ORIGINAL_DENIAL_NAMES
    ):
        raise SyntheticClockRejected("synthetic clock digest implementation changed")
    if (
        SyntheticClockWitness is not _WITNESS_TYPE
        or SyntheticClockSample is not _SAMPLE_TYPE
        or any(
            vars(_SAMPLE_TYPE).get(name) is not original
            for name, original in zip(
                _SAMPLE_FIELDS, _ORIGINAL_SAMPLE_FIELDS, strict=True,
            )
        )
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS, strict=True,
            )
        )
        or any(
            vars(_SAMPLE_TYPE).get(name) is not original
            for name, original in zip(
                _CARRIER_HOOKS, _ORIGINAL_SAMPLE_HOOKS, strict=True,
            )
        )
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _CARRIER_HOOKS, _ORIGINAL_WITNESS_HOOKS, strict=True,
            )
        )
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(_DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise SyntheticClockRejected("synthetic clock denial descriptor changed")


def _fields(value: SyntheticClockWitness) -> tuple[object, ...]:
    _denials_original()
    return (
        value.event_count, value.source_digest, value.last_wall_ms,
        value.last_monotonic_ns, value.chain_hash,
    )


def _check_witness(value: SyntheticClockWitness) -> None:
    _denials_original()
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
    _denials_original()


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
    _denials_original()
    if type(max_samples) is not int or not 1 <= max_samples <= _LIMIT:
        raise SyntheticClockRejected("invalid clock sample budget")
    if retained is not None and type(retained) is not SyntheticClockWitness:
        raise SyntheticClockRejected("retained clock witness requires exact type")
    _denials_original()
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
        _denials_original()
        # A false-valued denial getter can be reentrant: it must not rewrite
        # the just-checked witness or silently replace the original SHA
        # carrier after the last field comparison.
        def stable_result_fields() -> None:
            if (
                type(result) is not SyntheticClockWitness
                or _fields(result) != result_epoch
                or result.source_digest is not result_carriers[0]
                or result.chain_hash is not result_carriers[1]
            ):
                raise SyntheticClockRejected(
                    "constructed clock witness changed during sequence"
                )

        stable_result_fields()
        for flag in (
            "trusted_clock_verified", "dispatch_authorized",
            "automatic_replay_authorized",
        ):
            if getattr(result, flag) is not False:
                raise SyntheticClockRejected(
                    "constructed clock witness gained authority"
                )
            stable_result_fields()
            _denials_original()

    def assert_epoch() -> None:
        _denials_original()
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
            _denials_original()
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
            # The candidate's last false-valued authority getter may
            # reflectively alter its fields AFTER the earlier scalar checks.
            # Do not promote that altered candidate into the next link.
            if (
                _fields(candidate) != (seq, source, wall, mono, next_hash)
                or candidate.source_digest is not source
                or candidate.chain_hash is not next_hash
            ):
                raise SyntheticClockRejected(
                    "constructed clock chain link changed after denial"
                )
            _denials_original()
            result = candidate
            result_epoch = _fields(candidate)
            result_carriers = (candidate.source_digest, candidate.chain_hash)
            # A public frozen dataclass still has a patchable __eq__.
            # It must not be the sole authority for accepting/rejecting a
            # retained history prefix. Check the exact validated field vector
            # instead, without promoting this local digest to trusted time.
            if (
                retained is not None
                and seq == retained.event_count
                and _fields(result) != retained_epoch
            ):
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
