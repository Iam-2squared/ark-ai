"""Bounded offline identity bundle review for already-present local JSON files.

Each component must carry a separately retained file SHA-256. A bundle digest
binds their ordering, labels and locally verified metadata; it is NOT a
provenance attestation, billing approval, training gate or Candidate identity.
No files are created or changed. A double read is not an atomic OS snapshot.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .identity_artifact_verify import (
    LocalIdentityArtifactWitness,
    verify_local_identity_artifact,
)

_NAME = re.compile(r"[a-z][a-z0-9_]{0,47}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_COMPONENTS = 8
_DOMAIN = b"ARK-local-identity-bundle-v1\0"
_FLAGS = (
    "source_authenticated", "training_authorized",
    "candidate_generation_authorized", "protected_evaluation_authorized",
)


class LocalIdentityBundleRejected(ValueError):
    """A local file set or independently retained bundle digest disagrees."""


@dataclass(frozen=True, slots=True)
class LocalIdentityComponentPin:
    name: str
    path: Path
    retained_sha256: str


@dataclass(frozen=True, slots=True)
class LocalIdentityBundleWitness:
    components: tuple[tuple[str, str, int, tuple[str, ...]], ...]
    bundle_sha256: str

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def candidate_generation_authorized(self) -> bool:
        return False

    @property
    def protected_evaluation_authorized(self) -> bool:
        return False


_PIN_TYPE = LocalIdentityComponentPin
_WITNESS_TYPE = LocalIdentityBundleWitness
_ARTIFACT_WITNESS_TYPE = LocalIdentityArtifactWitness


def _hash(components: tuple[tuple[str, str, int, tuple[str, ...]], ...]) -> str:
    payload = json.dumps(
        components, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + payload).hexdigest()


def inspect_local_identity_bundle(
    pins: tuple[LocalIdentityComponentPin, ...],
) -> LocalIdentityBundleWitness:
    """Read a fixed set twice, detecting intervening routine file substitution.

    Only the independent per-component retained hashes can reject a
    same-process rewrite of byte content. No real model or GPU is accessed.
    """
    if (
        type(pins) is not tuple
        or not 1 <= len(pins) <= _MAX_COMPONENTS
        or any(type(pin) is not _PIN_TYPE for pin in pins)
    ):
        raise LocalIdentityBundleRejected("exact bounded bundle pins required")
    original = tuple(pins)
    captured = tuple((p.name, p.path, p.retained_sha256) for p in original)

    def stable() -> None:
        if (
            type(pins) is not tuple
            or len(pins) != len(original)
            or any(
                pin is not first
                or any(a is not b for a, b in zip(
                    (pin.name, pin.path, pin.retained_sha256),
                    values, strict=True,
                ))
                for pin, first, values in zip(
                    pins, original, captured, strict=True,
                )
            )
        ):
            raise LocalIdentityBundleRejected("bundle input carriers changed")

    stable()
    labels = tuple(fields[0] for fields in captured)
    paths = tuple(fields[1] for fields in captured)
    if (
        any(type(name) is not str or _NAME.fullmatch(name) is None for name in labels)
        or tuple(sorted(set(labels))) != labels
        or any(type(path) is not type(Path(".")) or not path.is_absolute()
               or ".." in path.parts or len(str(path)) > 4096 for path in paths)
        or len({str(path) for path in paths}) != len(paths)
        or any(
            type(sha) is not str or _SHA.fullmatch(sha) is None
            for _, _, sha in captured
        )
    ):
        raise LocalIdentityBundleRejected("bundle labels, paths or hashes invalid")
    components: list[tuple[str, str, int, tuple[str, ...]]] = []
    first_pass: list[LocalIdentityArtifactWitness] = []
    for name, path, sha in captured:
        stable()
        try:
            witness = verify_local_identity_artifact(path, retained_sha256=sha)
        except (ValueError, OSError) as exc:
            raise LocalIdentityBundleRejected("bundle component failed verification") from exc
        stable()
        if (
            type(witness) is not _ARTIFACT_WITNESS_TYPE
            or type(witness.artifact_sha256) is not str
            or witness.artifact_sha256 != sha
            or type(witness.artifact_bytes) is not int
            or not 0 < witness.artifact_bytes <= 8 * 1024 * 1024
            or type(witness.top_level_keys) is not tuple
            or any(type(k) is not str for k in witness.top_level_keys)
            or any(getattr(witness, flag) is not False for flag in _FLAGS)
        ):
            raise LocalIdentityBundleRejected("bundle component witness gained authority")
        first_pass.append(witness)
        components.append((name, sha, witness.artifact_bytes, witness.top_level_keys))
    # A component can be replaced while inspecting another file. All files
    # must still match the original independent pins at the end of the scan.
    for (_, path, sha), witness in zip(captured, first_pass, strict=True):
        stable()
        try:
            repeated = verify_local_identity_artifact(path, retained_sha256=sha)
        except (ValueError, OSError) as exc:
            raise LocalIdentityBundleRejected("bundle changed between reads") from exc
        stable()
        if (
            type(repeated) is not _ARTIFACT_WITNESS_TYPE
            or type(repeated.artifact_sha256) is not str
            or repeated.artifact_sha256 != sha
            or repeated.artifact_sha256 != witness.artifact_sha256
            or type(repeated.artifact_bytes) is not int
            or repeated.artifact_bytes != witness.artifact_bytes
            or type(repeated.top_level_keys) is not tuple
            or repeated.top_level_keys != witness.top_level_keys
            or any(getattr(repeated, flag) is not False for flag in _FLAGS)
        ):
            raise LocalIdentityBundleRejected(
                "bundle component changed between reads"
            )
        stable()
        if (
            repeated.artifact_sha256 != sha
            or repeated.artifact_bytes != witness.artifact_bytes
            or repeated.top_level_keys != witness.top_level_keys
        ):
            raise LocalIdentityBundleRejected(
                "bundle component changed after authority review"
            )
    stable()
    frozen = tuple(components)
    digest = _hash(frozen)
    report = LocalIdentityBundleWitness(frozen, digest)
    stable()
    if (
        type(report) is not _WITNESS_TYPE
        or report.components is not frozen
        or report.bundle_sha256 is not digest
        or any(getattr(report, flag) is not False for flag in _FLAGS)
    ):
        raise LocalIdentityBundleRejected("bundle report gained authority")
    # False-valued denial getters may rewrite this frozen report or a pin.
    stable()
    if (
        type(report) is not _WITNESS_TYPE
        or report.components is not frozen
        or report.bundle_sha256 is not digest
    ):
        raise LocalIdentityBundleRejected("bundle report changed after denial")
    return report


def verify_local_identity_bundle(
    report: LocalIdentityBundleWitness,
    pins: tuple[LocalIdentityComponentPin, ...],
    *,
    retained_bundle_sha256: str,
) -> None:
    """Re-read independently pinned local JSON; never issue training approval."""
    if (
        type(report) is not _WITNESS_TYPE
        or type(retained_bundle_sha256) is not str
        or _SHA.fullmatch(retained_bundle_sha256) is None
    ):
        raise LocalIdentityBundleRejected("exact bundle and retained root required")
    # Capture the original report carriers BEFORE any component verifier
    # callback. Matching values or local SHA-256 bytes cannot excuse a
    # reflected replacement by an equal-valued new tuple/string mid-review.
    original_components = report.components
    original_report_digest = report.bundle_sha256
    original_pins = tuple(pins) if type(pins) is tuple else ()
    pinned_fields = tuple(
        (pin.name, pin.path, pin.retained_sha256)
        for pin in original_pins if type(pin) is _PIN_TYPE
    )

    def stable_pins() -> None:
        if (
            type(pins) is not tuple
            or len(pins) != len(original_pins)
            or len(pinned_fields) != len(original_pins)
            or any(
                pin is not original
                or type(pin) is not _PIN_TYPE
                or any(
                    now is not initial for now, initial in zip(
                        (pin.name, pin.path, pin.retained_sha256),
                        fields, strict=True,
                    )
                )
                for pin, original, fields in zip(
                    pins, original_pins, pinned_fields, strict=True,
                )
            )
        ):
            raise LocalIdentityBundleRejected("bundle pin carrier changed")

    expected = inspect_local_identity_bundle(pins)
    stable_pins()

    def exact_report() -> bool:
        if (
            type(report) is not _WITNESS_TYPE
            or report.components is not original_components
            or report.bundle_sha256 is not original_report_digest
            or type(report.bundle_sha256) is not str
            or report.bundle_sha256 != retained_bundle_sha256
            or report.bundle_sha256 != expected.bundle_sha256
            or type(report.components) is not tuple
            or len(report.components) != len(expected.components)
        ):
            return False
        for actual, correct in zip(
            report.components, expected.components, strict=True,
        ):
            if (
                type(actual) is not tuple
                or len(actual) != 4
                or type(actual[0]) is not str
                or type(actual[1]) is not str
                or type(actual[2]) is not int
                or type(actual[3]) is not tuple
                or any(type(key) is not str for key in actual[3])
                or actual != correct
            ):
                return False
        return True

    if not exact_report():
        raise LocalIdentityBundleRejected("retained bundle root mismatch")
    for flag in _FLAGS:
        if getattr(report, flag) is not False:
            raise LocalIdentityBundleRejected("retained bundle gained authority")
    stable_pins()
    if not exact_report():
        raise LocalIdentityBundleRejected("retained bundle changed after denial")
    # A denial getter can also change on-disk bytes. A final bounded re-read
    # observes routine post-validation drift, but is not an atomic OS snapshot.
    latest = inspect_local_identity_bundle(pins)
    stable_pins()
    if (
        not exact_report()
        or type(latest) is not _WITNESS_TYPE
        or latest.components != expected.components
        or latest.bundle_sha256 != expected.bundle_sha256
    ):
        raise LocalIdentityBundleRejected("bundle files changed during verification")
